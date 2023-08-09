#!/usr/bin/python3
import argparse
import base64
import spectral.io.envi as envi
import io
import json
import numpy as np
import os
import pathlib
import pygubu
import redis
import sys
import traceback
import tkinter as tk
import tkinter.ttk as ttk

from datetime import datetime
from PIL import ImageTk, Image, ImageDraw
from tkinter import filedialog as fd
from tkinter import messagebox
from ttkSimpleDialog import ttkSimpleDialog
from happy.hsi_to_rgb.generate import normalize_data
from opex import ObjectPredictions, ObjectPrediction, Polygon, BBox
from operator import itemgetter

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "viewer.ui"

DIMENSIONS = "H: %d, W: %d, C: %d"


class ViewerApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # Main widget
        self.mainwindow = builder.get_object("toplevel", master)
        builder.connect_callbacks(self)
        self.mainwindow.iconphoto(False, tk.PhotoImage(file=str(PROJECT_PATH) + '/../logo.png'))
        self.mainwindow.bind("<Configure>", self.on_window_resize)

        # setting theme
        style = ttk.Style(self.mainwindow)
        style.theme_use('clam')

        # attach variables to app itself
        self.state_keep_aspectratio = None
        self.state_autodetect_channels = None
        self.state_annotation_color = None
        self.state_redis_host = None
        self.state_redis_port = None
        self.state_redis_pw = None
        self.state_redis_in = None
        self.state_redis_out = None
        self.state_marker_size = None
        self.state_marker_color = None
        self.state_min_obj_size = None
        self.state_scale_r = None
        self.state_scale_g = None
        self.state_scale_b = None
        self.state_export_with_annotations = None
        builder.import_variables(self)

        # reference components
        self.notebook = builder.get_object("notebook", master)
        # image
        self.frame_image = builder.get_object("frame_image", master)
        self.image_label = builder.get_object("label_image", master)
        # info
        self.text_info = builder.get_object("text_info", master)
        # options
        self.checkbutton_autodetect_channels = builder.get_object("checkbutton_autodetect_channels", master)
        self.checkbutton_keep_aspectratio = builder.get_object("checkbutton_keep_aspectratio", master)
        self.entry_annotation_color = builder.get_object("entry_annotation_color", master)
        self.entry_redis_host = builder.get_object("entry_redis_host", master)
        self.entry_redis_port = builder.get_object("entry_redis_port", master)
        self.entry_redis_in = builder.get_object("entry_redis_in", master)
        self.entry_redis_out = builder.get_object("entry_redis_out", master)
        self.entry_marker_size = builder.get_object("entry_marker_size", master)
        self.entry_marker_color = builder.get_object("entry_marker_color", master)
        self.entry_min_obj_size = builder.get_object("entry_min_obj_size", master)
        self.label_redis_connection = builder.get_object("label_redis_connection", master)
        self.button_sam_connect = builder.get_object("button_sam_connect", master)
        # log
        self.text_log = builder.get_object("text_log", master)
        # statusbar
        self.label_dims = builder.get_object("label_dims", master)
        self.red_scale = builder.get_object("scale_r", master)
        self.green_scale = builder.get_object("scale_g", master)
        self.blue_scale = builder.get_object("scale_b", master)
        self.red_scale_value = builder.get_object("label_r_value", master)
        self.green_scale_value = builder.get_object("label_g_value", master)
        self.blue_scale_value = builder.get_object("label_b_value", master)
        self.label_r_value = builder.get_object("label_r_value", master)
        self.label_g_value = builder.get_object("label_g_value", master)
        self.label_b_value = builder.get_object("label_b_value", master)

        # accelerators are just strings, we need to bind them to actual methods
        # https://tkinterexamples.com/events/keyboard/
        self.mainwindow.bind("<Control-o>", self.on_file_open_scan_click)
        self.mainwindow.bind("<Control-n>", self.on_file_clear_blackref)
        self.mainwindow.bind("<Control-r>", self.on_file_open_blackref)
        self.mainwindow.bind("<Control-N>", self.on_file_clear_whiteref)  # upper case N implies Shift key!
        self.mainwindow.bind("<Control-R>", self.on_file_open_whiteref)   # upper case R implies Shift key!
        self.mainwindow.bind("<Control-e>", self.on_file_exportimage_click)
        self.mainwindow.bind("<Alt-x>", self.on_file_close_click)
        self.mainwindow.bind("<Control-A>", self.on_tools_clear_annotations_click)
        self.mainwindow.bind("<Control-M>", self.on_tools_clear_markers_click)
        self.mainwindow.bind("<Control-L>", self.on_tools_remove_last_annotations_click)
        self.mainwindow.bind("<Control-s>", self.on_tools_sam_click)
        self.mainwindow.bind("<Control-p>", self.on_tools_polygon_click)

        # mouse events
        # https://tkinterexamples.com/events/mouse/
        self.image_label.bind("<Button-1>", self.on_image_click)
        self.label_r_value.bind("<Button-1>", self.on_label_r_click)
        self.label_g_value.bind("<Button-1>", self.on_label_g_click)
        self.label_b_value.bind("<Button-1>", self.on_label_b_click)

        # init some vars
        self.autodetect_channels = False
        self.keep_aspectratio = False
        self.last_blackref_dir = "."
        self.last_whiteref_dir = "."
        self.last_scan_dir = "."
        self.last_image_dir = "."
        self.data_scan = None
        self.data_blackref = None
        self.data_whiteref = None
        self.data_norm = None
        self.current_scan = None
        self.current_blackref = None
        self.current_whiteref = None
        self.photo_scan = None
        self.display_image = None
        self.redis_connection = None
        self.redis_pubsub = None
        self.redis_thread = None
        self.marker_points = []
        self.contours = []

    def run(self):
        self.mainwindow.mainloop()

    def log(self, msg):
        """
        Prints message on stdout.

        :param msg: the message to log
        :type msg: str
        """
        if msg != "":
            print(msg)
            if hasattr(self, "text_log") and (self.text_log is not None):
                self.text_log.insert(tk.END, "\n" + msg)

    def open_envi_file(self, title, initial_dir):
        """
        Allows the user to select an ENVI file.
        
        :param title: the title for the open dialog
        :type title: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        filetypes = (
            ('ENVI files', '*.hdr'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=filetypes)
        if filename == "":
            filename = None

        return filename

    def save_image_file(self, title, initial_dir):
        """
        Allows the user to select a PNG file for saving an image.
         
        :param title: the title to use for the save dialog
        :type title: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        filetypes = (
            ('PNG files', '*.png'),
            ('All files', '*.*')
        )

        filename = fd.asksaveasfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=filetypes)
        if filename == "":
            filename = None

        return filename

    def load_scan(self, filename, do_update=False):
        """
        Loads the specified ENVI scan file and displays it.

        :param filename: the scan to load
        :type filename: str
        :param do_update: whether to update the display
        :type do_update: bool
        """
        self.log("Loading scan: %s" % filename)
        img = envi.open(filename)
        self.data_scan = img.load()
        self.current_scan = filename
        self.reset_norm_data()

        # configure scales
        num_bands = self.data_scan.shape[2]
        self.red_scale.configure(to=num_bands - 1)
        self.green_scale.configure(to=num_bands - 1)
        self.blue_scale.configure(to=num_bands - 1)
        self.label_dims.configure(text=DIMENSIONS % self.data_scan.shape)

        # set r/g/b from default bands?
        if self.autodetect_channels:
            try:
                metadata = img.metadata
                if "default bands" in metadata:
                    bands = [int(x) for x in metadata["default bands"]]
                    r, g, b = bands
                    self.set_wavelengths(r, g, b)
            except:
                pass

        if do_update:
            self.update()

    def load_blackref(self, filename, do_update=True):
        """
        Loads the specified ENVI black reference file and updates the display.

        :param filename: the black reference to load
        :type filename: str
        :param do_update: whether to update the display
        :type do_update: bool
        """
        self.log("Loading black reference: %s" % filename)
        data = envi.open(filename).load()
        if data.shape != self.data_scan.shape:
            messagebox.showerror(
                "Error",
                "Black reference data should have the same shape as the scan data!\n"
                + "scan:" + str(self.data_scan.shape) + " != blackref:" + str(data.shape))
            return

        self.data_blackref = data
        self.current_blackref = filename
        self.reset_norm_data()

        if do_update:
            self.update()

    def load_whiteref(self, filename, do_update=True):
        """
        Loads the specified ENVI white reference file and updates the display.

        :param filename: the white reference to load
        :type filename: str
        :param do_update: whether to update the display
        :type do_update: bool
        """
        self.log("Loading white reference: %s" % filename)
        data = envi.open(filename).load()
        if data.shape != self.data_scan.shape:
            messagebox.showerror(
                "Error",
                "White reference data should have the same shape as the scan data!\n"
                + "scan:" + str(self.data_scan.shape) + " != whiteref:" + str(data.shape))
            return

        self.data_whiteref = data
        self.current_whiteref = filename
        self.reset_norm_data()

        if do_update:
            self.update()

    def reset_norm_data(self):
        """
        Resets the normalized data, forcing a recalculation.
        """
        self.data_norm = None

    def calc_norm_data(self):
        """
        Calculates the normalized data.
        """
        if self.data_norm is not None:
            return
        if self.data_scan is not None:
            self.log("Calculating...")
            self.data_norm = self.data_scan
            # subtract black reference
            if self.data_blackref is not None:
                self.data_norm = self.data_norm - self.data_blackref
            # divide by white reference
            if self.data_whiteref is not None:
                self.data_norm = self.data_norm / self.data_whiteref

    def set_wavelengths(self, r, g, b):
        """
        Sets the wavelengths to use.

        :param r: the red channel
        :type r: int
        :param g: the green channel
        :type g: int
        :param b: the blue channel
        :type b: int
        """
        # adjust "to" if necessary
        if self.red_scale.cget("to") < r:
            self.red_scale.configure(to=r)
        if self.green_scale.cget("to") < g:
            self.green_scale.configure(to=g)
        if self.blue_scale.cget("to") < b:
            self.blue_scale.configure(to=b)
        self.log("Setting RGB: r=%d, g=%d, b=%d" % (r, g, b))
        self.red_scale.set(r)
        self.green_scale.set(g)
        self.blue_scale.set(b)

    def get_data_dims(self):
        """
        Returns the dimensions of the loaded data.

        :return: the tuple (w,h) of the data, None if no data
        :rtype: tuple
        """
        if self.data_norm is None:
            return None
        else:
            return self.data_norm.shape[1], self.data_norm.shape[0]

    def get_image_label_dims(self):
        """
        Returns the dimensions of the image label displaying the data.

        :return: the tuple (w,h) of the image label, None if no data
        :rtype: tuple
        """
        if self.data_norm is None:
            return None
        else:
            return self.frame_image.winfo_width() - 10, self.frame_image.winfo_height() - 10

    def fit_image_into_dims(self, available_width, available_height):
        """
        Fits the image into the specified available dimensions and returns the calculated dimensions.

        :param available_width: the width to scale to, skips calculation if 0 or less
        :type available_width: int
        :param available_height: the height to scale to
        :type available_height: int
        :return: the scaled dimensions (w,h), None if invalid width/height
        :rtype: tuple
        """
        if available_width < 1:
            return None
        if available_height < 1:
            return None

        # keep aspect ratio?
        if self.keep_aspectratio:
            available_aspect = available_width / available_height
            img_width, img_height = self.get_data_dims()
            img_aspect = img_width / img_height
            if img_aspect > available_aspect:
                scale = img_width / available_width
            else:
                scale = img_height / available_height
            actual_width = int(img_width / scale)
            actual_height = int(img_height / scale)
        else:
            actual_width = available_width
            actual_height = available_height

        return actual_width, actual_height

    def get_scaled_image(self, width, height):
        """
        Computes the scaled image and returns it.

        :param width: the width to scale to
        :type width: int
        :param height: the height to scale to
        :type height: int
        :return: the scaled image
        """
        if self.display_image is not None:
            image = Image.fromarray(self.display_image)
            image = image.resize((width, height), Image.LANCZOS)
            return image
        else:
            return None

    def get_current_image_dims(self):
        """
        Returns the current dimensions for the image.

        :return: the dimensions as tuple (w,h) or None if not available
        :rtype: tuple
        """
        if self.data_norm is None:
            return None
        if self.keep_aspectratio:
            result = (self.data_norm.shape[1], self.data_norm.shape[0])
        else:
            result = (self.frame_image.winfo_width() - 10, self.frame_image.winfo_height() - 10)
        return result

    def resize_image_label(self):
        """
        Computes the scaled image and updates the GUI.
        """
        dims = self.get_image_label_dims()
        if dims is None:
            return
        dims = self.fit_image_into_dims(dims[0], dims[1])
        if dims is None:
            return
        image = self.get_scaled_image(dims[0], dims[1])
        if image is not None:
            image_sam_points = self.calc_marker_points_overlay(dims[0], dims[1])
            if image_sam_points is not None:
                image.paste(image_sam_points, (0, 0), image_sam_points)
            image_contours = self.calc_contours_overlay(dims[0], dims[1])
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)
            self.photo_scan = ImageTk.PhotoImage(image=image)
            self.image_label.config(image=self.photo_scan)

    def calc_marker_points_overlay(self, width, height):
        """
        Generates a new overlay image for marker points and returns it.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the generated overlay
        """
        image = Image.new("RGBA", (width, height), color=None)
        draw = ImageDraw.Draw(image)
        marker_size = int(self.entry_marker_size.get())
        for point in self.marker_points:
            point_a = (point[0]*width, point[1]*height)
            bbox = [point_a[0] - marker_size // 2, point_a[1] - marker_size // 2, point_a[0] + marker_size // 2, point_a[1] + marker_size // 2]
            draw.ellipse(bbox, outline=self.entry_marker_color.get())
        return image

    def calc_absolute_contours(self, width, height):
        """
        Calculates the absolute contours from the normalized ones.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the absolute contours
        :rtype: list
        """
        result = []
        for contours in self.contours:
            contours_a = []
            for contour in contours:
                contour_a = []
                for coord in contour:
                    contour_a.append((int(coord[0]*width), int(coord[1]*height)))
                contours_a.append(contour_a)
            result.append(contours_a)
        return result

    def calc_contours_overlay(self, width, height):
        """
        Generates a new overlay image for contours and returns it.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the generated overlay
        """
        image = Image.new("RGBA", (width, height), color=None)
        draw = ImageDraw.Draw(image)
        for contours in self.calc_absolute_contours(width, height):
            for contour in contours:
                draw.polygon(contour, outline=self.entry_annotation_color.get())
        return image

    def contours_to_opex(self, width, height):
        """
        Turns the contours into OPEX format and returns it.

        :param width: the width of the image to use
        :type width: int
        :param height: the height of the image to use
        :type height: int
        :return: the generated OPEX data structure, None if no contours available
        :rtype: ObjectPredictions
        """
        if len(self.contours) == 0:
            return None
        start_time = datetime.now()
        objs = []
        for contours in self.calc_absolute_contours(width, height):
            for contour in contours:
                # https://stackoverflow.com/a/13145419/4698227
                min_xy = min(contour, key=itemgetter(0))[0], min(contour, key=itemgetter(1))[1]
                max_xy = max(contour, key=itemgetter(0))[0], max(contour, key=itemgetter(1))[1]
                bbox = BBox(left=min_xy[0], top=min_xy[1], right=max_xy[0], bottom=max_xy[1])
                poly = Polygon(points=contour)
                pred = ObjectPrediction(label="object", bbox=bbox, polygon=poly)
                objs.append(pred)
        result = ObjectPredictions(id=str(start_time), timestamp=str(start_time), objects=objs)
        return result

    def update_image(self):
        """
        Updates the image.
        """
        if self.data_scan is None:
            return

        self.calc_norm_data()

        red_band = self.data_norm[:, :, int(self.red_scale.get())]
        green_band = self.data_norm[:, :, int(self.green_scale.get())]
        blue_band = self.data_norm[:, :, int(self.blue_scale.get())]

        norm_red = normalize_data(red_band)
        norm_green = normalize_data(green_band)
        norm_blue = normalize_data(blue_band)

        rgb_image = np.dstack((norm_red, norm_green, norm_blue))
        self.display_image = (rgb_image * 255).astype(np.uint8)

        self.resize_image_label()
        self.log("")

    def update_info(self):
        """
        Updates the information.
        """
        info = ""
        # scan
        info += "Scan:\n"
        if self.current_scan is None:
            info += "-none-"
        else:
            info += self.current_scan + "\n" + str(self.data_scan.shape)
        # black
        info += "\n\nBlack reference:\n"
        if self.current_blackref is None:
            info += "-none-"
        else:
            info += self.current_blackref + "\n" + str(self.data_blackref.shape)
        # white
        info += "\n\nWhite reference:\n"
        if self.current_whiteref is None:
            info += "-none-"
        else:
            info += self.current_whiteref + "\n" + str(self.data_whiteref.shape)
        # update
        self.text_info.delete(1.0, tk.END)
        self.text_info.insert(tk.END, info)

    def update(self):
        """
        Updates image and info.
        """
        self.update_image()
        self.update_info()

    def set_keep_aspectratio(self, value):
        """
        Sets whether to keep the aspect ratio or not.

        :param value: whether to keep
        :type value: bool
        """
        self.keep_aspectratio = value
        self.state_keep_aspectratio.set(1 if value else 0)

    def set_autodetect_channels(self, value):
        """
        Sets whether to auto-detect the channels from the meta-data or use the manually supplied ones.

        :param value: whether to auto-detect
        :type value: bool
        """
        self.autodetect_channels = value
        self.state_autodetect_channels.set(1 if value else 0)

    def set_annotation_color(self, color):
        """
        Sets the color to use for the annotations like contours.

        :param color: the hex color to use (eg #ff0000)
        :type color: str
        """
        self.log("Setting annotation color: %s" % color)
        self.state_annotation_color.set(color)

    def set_redis_connection(self, host, port, pw, send, receive):
        """
        Sets the redis connection parameters.
        
        :param host: the redis host
        :type host: str
        :param port: the redis port
        :type port: int
        :param pw: the password to use, ignored if None or empty string
        :type pw: str
        :param send: the channel to send the images to
        :type send: str
        :param receive: the channel to receive the annotations from
        :type receive: str 
        """
        if pw is None:
            pw = ""
        self.log("Setting Redis connection: host=%s port=%d in=%s out%s" % (host, port, send, receive))
        self.state_redis_host.set(host)
        self.state_redis_port.set(port)
        self.state_redis_pw.set(pw)
        self.state_redis_in.set(send)
        self.state_redis_out.set(receive)

    def set_sam_options(self, marker_size, marker_color, min_obj_size):
        """
        Sets the options for SAM.

        :param marker_size: the size of the marker
        :type marker_size: int
        :param marker_color: the color of the markers (hex color, eg #ff0000)
        :type marker_color: str
        :param min_obj_size: the minimum size (with and height) the contours objects must have (<= 0 is unbounded)
        :type min_obj_size: int
        """
        if min_obj_size < -1:
            min_obj_size = -1
        self.log("Setting SAM options: marker_size=%d marker_color=%s min_obj_size=%d" % (marker_size, marker_color, min_obj_size))
        self.state_marker_size.set(marker_size)
        self.state_marker_color.set(marker_color)
        self.state_min_obj_size.set(min_obj_size)

    def on_file_open_scan_click(self, event=None):
        """
        Allows the user to select a black reference ENVI file.
        """
        filename = self.open_envi_file('Open scan', self.last_scan_dir)

        if filename is not None:
            self.last_scan_dir = os.path.dirname(filename)
            self.load_scan(filename)

    def on_file_clear_blackref(self, event=None):
        if self.data_blackref is not None:
            self.data_blackref = None
            self.current_blackref = None
            self.reset_norm_data()
            self.update()

    def on_file_open_blackref(self, event=None):
        """
        Allows the user to select a black reference ENVI file.
        """
        if self.data_scan is None:
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_envi_file('Open black reference', self.last_blackref_dir)

        if filename is not None:
            self.last_blackref_dir = os.path.dirname(filename)
            self.load_blackref(filename)

    def on_file_clear_whiteref(self, event=None):
        if self.data_whiteref is not None:
            self.data_whiteref = None
            self.current_whiteref = None
            self.reset_norm_data()
            self.update()

    def on_file_open_whiteref(self, event=None):
        """
        Allows the user to select a white reference ENVI file.
        """
        if self.data_scan is None:
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_envi_file('Open white reference', self.last_whiteref_dir)

        if filename is not None:
            self.last_whiteref_dir = os.path.dirname(filename)
            self.load_whiteref(filename)

    def on_file_exportimage_click(self, event=None):
        """
        Allows the user to select a PNG file for saving the false color RGB to.
        """
        if self.keep_aspectratio:
            dims = self.get_data_dims()
        else:
            dims = self.get_image_label_dims()
        if dims is None:
            return
        dims = self.fit_image_into_dims(dims[0], dims[1])
        image = self.get_scaled_image(dims[0], dims[1])
        if image is None:
            return

        # include annotations?
        if self.state_export_with_annotations.get() == 1:
            image_sam_points = self.calc_marker_points_overlay(dims[0], dims[1])
            if image_sam_points is not None:
                image.paste(image_sam_points, (0, 0), image_sam_points)
            image_contours = self.calc_contours_overlay(dims[0], dims[1])
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)

        filename = self.save_image_file('Save image', self.last_image_dir)
        if filename is not None:
            self.last_image_dir = os.path.dirname(filename)
            image.save(filename)
            annotations = self.contours_to_opex(dims[0], dims[1])
            if annotations is not None:
                annotations.save_json_to_file(os.path.splitext(filename)[0] + ".json")

    def on_file_close_click(self, event=None):
        self.mainwindow.quit()

    def on_autodetect_channels_click(self):
        self.autodetect_channels = self.state_autodetect_channels.get()

    def on_keep_aspectratio_click(self):
        self.keep_aspectratio = self.state_keep_aspectratio.get()
        self.update_image()

    def on_scale_r_changed(self, event):
        self.red_scale_value.configure(text=str(self.state_scale_r.get()))
        self.update_image()

    def on_scale_g_changed(self, event):
        self.green_scale_value.configure(text=str(self.state_scale_g.get()))
        self.update_image()

    def on_scale_b_changed(self, event):
        self.blue_scale_value.configure(text=str(self.state_scale_b.get()))
        self.update_image()

    def on_window_resize(self, event):
        self.resize_image_label()

    def on_image_click(self, event=None):
        # no modifier -> add
        if event.state == 16:
            x = event.x / self.image_label.winfo_width()
            y = event.y / self.image_label.winfo_height()
            point = (x, y)
            self.marker_points.append(point)
            self.log("Marker point added: %s" % str(point))
        # ctrl -> clear
        elif event.state == 20:
            self.marker_points = []
            self.log("Marker points cleared")
        # update image
        self.update_image()

    def on_label_r_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Red channel",
            prompt="Please enter the channel to use as Red:",
            initialvalue=self.state_scale_r.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.red_scale.set(new_channel)

    def on_label_g_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Green channel",
            prompt="Please enter the channel to use as Green:",
            initialvalue=self.state_scale_g.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.green_scale.set(new_channel)

    def on_label_b_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Blue channel",
            prompt="Please enter the channel to use as Blue:",
            initialvalue=self.state_scale_b.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.blue_scale.set(new_channel)

    def on_tools_clear_annotations_click(self, event=None):
        if (len(self.contours) > 0) or (len(self.marker_points) > 0):
            self.contours = []
            self.marker_points = []
            self.update_image()
            self.log("Annotations/marker points cleared")
        else:
            self.log("No annotations/marker points to clear")

    def on_tools_clear_markers_click(self, event=None):
        if len(self.marker_points) > 0:
            self.marker_points = []
            self.update_image()
            self.log("Marker points cleared")
        else:
            self.log("No marker points to clear")

    def on_tools_remove_last_annotations_click(self, event=None):
        if len(self.contours) > 0:
            self.contours.pop()
            self.update_image()
            self.log("Last annotations removed")
        else:
            self.log("No annotations to remove")

    def on_tools_sam_click(self, event=None):
        if self.redis_connection is None:
            messagebox.showerror("Error", "Not connected to Redis server, cannot communicate with SAM!")
            self.notebook.select(2)
            return
        if len(self.marker_points) == 0:
            messagebox.showerror("Error", "No prompt points for SAM collected!")
            return

        # image
        dims = self.get_image_label_dims()
        if dims is None:
            messagebox.showerror("Error", "No image available!")
            return
        dims = self.fit_image_into_dims(dims[0], dims[1])
        if dims is None:
            messagebox.showerror("Error", "No image available!")
            return
        img = self.get_scaled_image(dims[0], dims[1])
        if img is None:
            messagebox.showerror("Error", "No image available!")
            return
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        content = buf.getvalue()

        # collected points
        points = [(int(x * self.image_label.winfo_width()), int(y * self.image_label.winfo_height()))
                  for x, y in self.marker_points]
        self.log("Sending image to SAM using prompt point(s): %s" % str(points))
        prompt = {
            "points": [
                {
                    "x": item[0],
                    "y": item[1],
                    "label": 1
                } for item in points
            ]
        }

        # create message and send
        d = {
            "image": base64.encodebytes(content).decode("ascii"),
            "prompt": prompt,
        }
        self.redis_connection.publish(self.state_redis_in.get(), json.dumps(d))

        # empty points
        self.marker_points = []

        self.redis_pubsub = self.redis_connection.pubsub()

        # handler for listening/outputting
        def anon_handler(message):
            self.log("SAM data received")
            d = json.loads(message['data'].decode())
            # mask
            png_data = base64.decodebytes(d["mask"].encode())
            mask = Image.open(io.BytesIO(png_data))
            width, height = mask.size
            # contours to normalized contours
            contours_n = []
            contours = d["contours"]
            min_obj_size = self.state_min_obj_size.get()
            discarded = 0
            for contour in contours:
                points_n = []
                minx = sys.maxsize
                maxx = 0
                miny = sys.maxsize
                maxy = 0
                for coords in contour:
                    x, y = coords
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
                    points_n.append((x / width, y / height))
                # minimum size?
                keep = (min_obj_size <= 0)
                if (min_obj_size > 0) and (maxx - minx + 1 > min_obj_size) and (maxy - miny + 1 > min_obj_size):
                    keep = True
                if keep:
                    contours_n.append(points_n)
                else:
                    discarded += 1
            self.log("# contours: %d" % len(contours_n))
            if discarded > 0:
                self.log("# contours too small (< %d): %d" % (min_obj_size, discarded))
            self.contours.append(contours_n)
            # stop/close pubsub
            self.redis_thread.stop()
            self.redis_pubsub.close()
            self.redis_pubsub = None
            # update contours/image
            self.resize_image_label()

        # subscribe and start listening
        self.redis_pubsub.psubscribe(**{self.state_redis_out.get(): anon_handler})
        self.redis_thread = self.redis_pubsub.run_in_thread(sleep_time=0.001)

    def on_tools_polygon_click(self, event=None):
        if len(self.marker_points) <= 3:
            messagebox.showerror("Error", "At least three marker points necessary to create a polygon!")
            return

        contours = [self.marker_points[:]]
        self.contours.append(contours)
        self.marker_points = []
        self.log("Polygon added")
        self.update_image()

    def on_button_sam_connect_click(self, event=None):
        if self.redis_connection is not None:
            self.log("Disconnecting Redis...")
            self.button_sam_connect.configure(text="Connect")
            try:
                self.redis_connection.close()
                self.redis_connection = None
                self.label_redis_connection.configure(text="Disconnected")
            except:
                pass
        else:
            self.log("Connecting Redis...")
            pw = self.state_redis_pw.get()
            if pw == "":
                pw = None
            self.redis_connection = redis.Redis(host=self.state_redis_host.get(), port=self.state_redis_port.get(), password=pw)
            try:
                self.redis_connection.ping()
                self.label_redis_connection.configure(text="Connected")
                self.button_sam_connect.configure(text="Disconnect")
            except:
                traceback.print_exc()
                self.label_redis_connection.configure(text="Failed to connect")
                self.redis_connection = None

    def on_button_log_clear_click(self, event=None):
        self.text_log.delete(1.0, tk.END)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="ENVI Hyper-spectral Image Viewer.\nOffers contour detection using SAM (Segment-Anything: https://github.com/waikato-datamining/pytorch/tree/master/segment-anything)",
        prog="happy-viewer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", "--scan", type=str, help="Path to the scan file (ENVI format)", required=False)
    parser.add_argument("-f", "--black_reference", type=str, help="Path to the black reference file (ENVI format)", required=False)
    parser.add_argument("-w", "--white_reference", type=str, help="Path to the white reference file (ENVI format)", required=False)
    parser.add_argument("-r", "--red", metavar="INT", help="the wave length to use for the red channel", default=0, type=int, required=False)
    parser.add_argument("-g", "--green", metavar="INT", help="the wave length to use for the green channel", default=0, type=int, required=False)
    parser.add_argument("-b", "--blue", metavar="INT", help="the wave length to use for the blue channel", default=0, type=int, required=False)
    parser.add_argument("--autodetect_channels", action="store_true", help="whether to determine the channels from the meta-data (overrides the manually specified channels)", required=False)
    parser.add_argument("--keep_aspectratio", action="store_true", help="whether to keep the aspect ratio", required=False)
    parser.add_argument("--annotation_color", metavar="HEXCOLOR", help="the color to use for the annotations like contours (hex color)", default="#ff0000", required=False)
    parser.add_argument("--redis_host", metavar="HOST", type=str, help="The Redis host to connect to (IP or hostname)", default="localhost", required=False)
    parser.add_argument("--redis_port", metavar="PORT", type=int, help="The port the Redis server is listening on", default=6379, required=False)
    parser.add_argument("--redis_pw", metavar="PASSWORD", type=str, help="The password to use with the Redis server", default=None, required=False)
    parser.add_argument("--redis_in", metavar="CHANNEL", type=str, help="The channel that SAM is receiving images on", default="sam_in", required=False)
    parser.add_argument("--redis_out", metavar="CHANNEL", type=str, help="The channel that SAM is broadcasting the detections on", default="sam_out", required=False)
    parser.add_argument("--redis_connect", action="store_true", help="whether to immediately connect to the Redis host", required=False)
    parser.add_argument("--sam_marker_size", metavar="INT", help="The size in pixels for the SAM points", default=7, type=int, required=False)
    parser.add_argument("--sam_marker_color", metavar="HEXCOLOR", help="the color to use for the SAM points (hex color)", default="#ff0000", required=False)
    parser.add_argument("--sam_min_obj_size", metavar="INT", help="The minimum size that SAM contours need to have (<= 0 for no minimum)", default=-1, type=int, required=False)
    parsed = parser.parse_args(args=args)
    app = ViewerApp()
    if parsed.autodetect_channels:
        app.set_autodetect_channels(True)
    else:
        app.set_autodetect_channels(False)
        app.set_wavelengths(parsed.red, parsed.green, parsed.blue)
    app.set_keep_aspectratio(parsed.keep_aspectratio)
    app.set_annotation_color(parsed.annotation_color)
    app.set_redis_connection(parsed.redis_host, parsed.redis_port, parsed.redis_pw, parsed.redis_in, parsed.redis_out)
    app.set_sam_options(parsed.sam_marker_size, parsed.sam_marker_color, parsed.sam_min_obj_size)
    if parsed.redis_connect:
        app.button_sam_connect.invoke()
    if parsed.scan is not None:
        app.load_scan(parsed.scan, do_update=False)
        if parsed.black_reference is not None:
            app.load_blackref(parsed.black_reference, do_update=False)
        if parsed.white_reference is not None:
            app.load_whiteref(parsed.white_reference, do_update=False)
        app.update()
    app.run()


def sys_main() -> int:
    """
    Runs the main function using the system cli arguments, and
    returns a system error code.

    :return: 0 for success, 1 for failure.
    """
    try:
        main()
        return 0
    except Exception:
        print(traceback.format_exc())
        return 1


if __name__ == '__main__':
    main()
