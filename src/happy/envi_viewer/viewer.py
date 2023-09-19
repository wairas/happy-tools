#!/usr/bin/python3
import argparse
import copy
import io
import json
import matplotlib.pyplot as plt
import os
import pathlib
import pygubu
import traceback
import tkinter as tk
import tkinter.ttk as ttk

from PIL import ImageTk, Image
from tkinter import filedialog as fd
from tkinter import messagebox
from ttkSimpleDialog import ttkSimpleDialog
from happy.envi_viewer._contours import ContoursManager, Contour
from happy.envi_viewer._data import DataManager
from happy.envi_viewer._markers import MarkersManager
from happy.envi_viewer._redis import SamManager
from happy.envi_viewer._session import SessionManager, PROPERTIES

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
        self.state_check_scan_dimensions = None
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
        self.checkbutton_check_scan_dimenions = builder.get_object("checkbutton_check_scan_dimensions", master)
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
        self.image_label.bind("<Button-1>", self.on_image_click)
        self.label_r_value.bind("<Button-1>", self.on_label_r_click)
        self.label_g_value.bind("<Button-1>", self.on_label_g_click)
        self.label_b_value.bind("<Button-1>", self.on_label_b_click)

        # init some vars
        self.photo_scan = None
        self.session = SessionManager()
        self.data = DataManager()
        self.last_dims = None
        self.markers = MarkersManager()
        self.contours = ContoursManager()
        self.sam = SamManager()

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
        self.markers.clear()
        self.contours.clear()

        if self.data.has_scan():
            self.last_dims = self.data.scan_data.shape

        self.log("Loading scan: %s" % filename)
        warning = self.data.set_scan(filename)
        if warning is not None:
            messagebox.showerror("Warning", warning)

        # different dimensions?
        if self.session.check_scan_dimensions:
            if (self.last_dims is not None) and (self.data.has_scan()):
                if self.last_dims != self.data.scan_data.shape:
                    warning = "Different data dimensions detected: last=%s, new=%s" % (str(self.last_dims), str(self.data.scan_data.shape))
                    messagebox.showwarning("Different dimensions", warning)

        # configure scales
        num_bands = self.data.get_num_bands()
        self.red_scale.configure(to=num_bands - 1)
        self.green_scale.configure(to=num_bands - 1)
        self.blue_scale.configure(to=num_bands - 1)
        self.label_dims.configure(text=DIMENSIONS % self.data.scan_data.shape)

        # set r/g/b from default bands?
        if self.session.autodetect_channels:
            try:
                metadata = self.data.scan_img.metadata
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
        error = self.data.set_blackref(filename)
        if error is not None:
            messagebox.showerror("Error", error)
            return
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
        error = self.data.set_whiteref(filename)
        if error is not None:
            messagebox.showerror("Error", error)
            return
        if do_update:
            self.update()

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

    def get_image_label_dims(self):
        """
        Returns the dimensions of the image label displaying the data.

        :return: the tuple (w,h) of the image label, None if no data
        :rtype: tuple
        """
        if self.data.norm_data is None:
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
        if self.session.keep_aspectratio:
            available_aspect = available_width / available_height
            img_width, img_height = self.data.dims()
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
        if self.data.display_image is not None:
            image = Image.fromarray(self.data.display_image)
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
        if self.data.norm_data is None:
            return None
        if self.session.keep_aspectratio:
            result = (self.data.norm_data.shape[1], self.data.norm_data.shape[0])
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
            image_sam_points = self.markers.to_overlay(dims[0], dims[1], int(self.entry_marker_size.get()), self.entry_marker_color.get())
            if image_sam_points is not None:
                image.paste(image_sam_points, (0, 0), image_sam_points)
            image_contours = self.contours.to_overlay(dims[0], dims[1], self.entry_annotation_color.get())
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)
            self.photo_scan = ImageTk.PhotoImage(image=image)
            self.image_label.config(image=self.photo_scan)

    def update_image(self):
        """
        Updates the image.
        """
        self.data.update_image(int(self.red_scale.get()), int(self.green_scale.get()), int(self.blue_scale.get()), self.log)
        self.resize_image_label()
        self.log("")

    def update_info(self):
        """
        Updates the information.
        """
        info = ""
        # scan
        info += "Scan:\n"
        if self.data.scan_file is None:
            info += "-none-"
        else:
            info += self.data.scan_file + "\n" + str(self.data.scan_data.shape)
        # black
        info += "\n\nBlack reference:\n"
        if self.data.blackref_file is None:
            info += "-none-"
        else:
            info += self.data.blackref_file + "\n" + str(self.data.blackref_data.shape)
        # white
        info += "\n\nWhite reference:\n"
        if self.data.whiteref_file is None:
            info += "-none-"
        else:
            info += self.data.whiteref_file + "\n" + str(self.data.whiteref_data.shape)
        # wave lengths
        info += "\n\nWave lengths:\n"
        if len(self.data.get_wavelengths()) == 0:
            info += "-none-"
        else:
            info += "index\twave length\n"
            for i in self.data.get_wavelengths():
                if i in self.data.get_wavelengths():
                    info += str(i) + "\t" + self.data.get_wavelengths()[i] + "\n"
        # other metadata
        info += "\n\nOther meta-data:\n"
        if not self.data.has_scan():
            info += "-none-"
        else:
            metadata = self.data.scan_img.metadata
            for k in metadata:
                if k == "wavelength":
                    continue
                else:
                    info += "- %s: %s\n" % (k, str(metadata[k]))

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
        self.session.keep_aspectratio = value
        self.state_keep_aspectratio.set(1 if value else 0)

    def set_autodetect_channels(self, value):
        """
        Sets whether to auto-detect the channels from the meta-data or use the manually supplied ones.

        :param value: whether to auto-detect
        :type value: bool
        """
        self.session.autodetect_channels = value
        self.state_autodetect_channels.set(1 if value else 0)

    def set_check_scan_dimensions(self, value):
        """
        Sets whether to compare dimensions of subsequent scans and display a warning when they differ.

        :param value: whether to check dimensions
        :type value: bool
        """
        self.session.check_scan_dimensions = value
        self.state_check_scan_dimensions.set(1 if value else 0)

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

    def add_marker(self, event):
        """
        Adds a marker using the event coordinates.

        :param event: the event that triggered the adding
        """
        x = event.x / self.image_label.winfo_width()
        y = event.y / self.image_label.winfo_height()
        point = (x, y)
        self.markers.add(point)
        self.log("Marker point added: %s" % str(point))
        self.update_image()

    def set_label(self, event):
        """
        Prompts the user to enter a label for the contours that contain the event's position.

        :param event: the event that triggered the label setting
        """
        x = event.x / self.image_label.winfo_width()
        y = event.y / self.image_label.winfo_height()
        contours = self.contours.contains(x, y)
        if len(contours) > 0:
            labels = set([x.label for x in contours])
            if len(contours) > 1:
                text = "Please enter the label to apply to %d contours:" % len(contours)
            else:
                text = "Please enter the label"
            new_label = ttkSimpleDialog.askstring(
                title="Object label",
                prompt=text,
                initialvalue="" if (len(labels) != 1) else list(labels)[0],
                parent=self.mainwindow)
            if new_label is not None:
                for contour in contours:
                    contour.label = new_label
                self.update_image()

    def clear_markers(self):
        """
        Clears all markers.
        """
        self.markers.clear()
        self.log("Marker points cleared")

    def state_to_session(self):
        """
        Transfers the current state in the UI to the session manager.
        """
        self.session.autodetect_channels = (self.state_autodetect_channels.get() == 1)
        self.session.keep_aspectratio = (self.state_keep_aspectratio.get() == 1)
        self.session.check_scan_dimensions = (self.state_check_scan_dimensions.get() == 1)
        # last_blackref_dir
        # last_whiteref_dir
        # last_scan_dir
        # last_image_dir
        self.session.scale_r = self.state_scale_r.get()
        self.session.scale_g = self.state_scale_g.get()
        self.session.scale_b = self.state_scale_b.get()
        self.session.annotation_color = self.state_annotation_color.get()
        self.session.redis_host = self.state_redis_host.get()
        self.session.redis_port = self.state_redis_port.get()
        self.session.redis_pw = self.state_redis_pw.get()
        self.session.redis_in = self.state_redis_in.get()
        self.session.redis_out = self.state_redis_out.get()
        self.session.marker_size = self.state_marker_size.get()
        self.session.marker_color = self.state_marker_color.get()
        self.session.min_obj_size = self.state_min_obj_size.get()

    def session_to_state(self):
        """
        Transfers the session data to the UI.
        """
        self.state_autodetect_channels.set(1 if self.session.autodetect_channels else 0)
        self.state_keep_aspectratio.set(1 if self.session.keep_aspectratio else 0)
        self.state_check_scan_dimensions.set(1 if self.session.check_scan_dimensions else 0)
        # last_blackref_dir
        # last_whiteref_dir
        # last_scan_dir
        # last_image_dir
        self.state_scale_r.set(self.session.scale_r)
        self.state_scale_g.set(self.session.scale_g)
        self.state_scale_b.set(self.session.scale_b)
        self.state_annotation_color.set(self.session.annotation_color)
        self.state_redis_host.set(self.session.redis_host)
        self.state_redis_port.set(self.session.redis_port)
        self.state_redis_pw.set(self.session.redis_pw)
        self.state_redis_in.set(self.session.redis_in)
        self.state_redis_out.set(self.session.redis_out)
        self.state_marker_size.set(self.session.marker_size)
        self.state_marker_color.set(self.session.marker_color)
        self.state_min_obj_size.set(self.session.min_obj_size)

    def scale_to_text(self, index):
        """
        Generates the text for the scale label (index: wavelength).

        :param index: the index on the scale
        :type index: int
        :return: the generated text
        :rtype: str
        """
        if not self.data.has_scan():
            return str(index)
        try:
            return str(index) + ": " + str(self.data.get_wavelengths()[index])
        except:
            return str(index)

    def on_file_open_scan_click(self, event=None):
        """
        Allows the user to select a black reference ENVI file.
        """
        filename = self.open_envi_file('Open scan', self.session.last_scan_dir)

        if filename is not None:
            self.session.last_scan_dir = os.path.dirname(filename)
            self.load_scan(filename, do_update=True)

    def on_file_clear_blackref(self, event=None):
        if self.data.has_blackref():
            self.log("Clearing black reference")
            self.data.clear_blackref()
            self.update()

    def on_file_open_blackref(self, event=None):
        """
        Allows the user to select a black reference ENVI file.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_envi_file('Open black reference', self.session.last_blackref_dir)

        if filename is not None:
            self.session.last_blackref_dir = os.path.dirname(filename)
            self.load_blackref(filename, do_update=True)

    def on_file_clear_whiteref(self, event=None):
        if self.data.has_whiteref():
            self.log("Clearing white reference")
            self.data.clear_whiteref()
            self.update()

    def on_file_open_whiteref(self, event=None):
        """
        Allows the user to select a white reference ENVI file.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_envi_file('Open white reference', self.session.last_whiteref_dir)

        if filename is not None:
            self.session.last_whiteref_dir = os.path.dirname(filename)
            self.load_whiteref(filename, do_update=True)

    def on_file_exportimage_click(self, event=None):
        """
        Allows the user to select a PNG file for saving the false color RGB to.
        """
        if self.session.keep_aspectratio:
            dims = self.data.dims()
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
            image_sam_points = self.markers.to_overlay(dims[0], dims[1], int(self.entry_marker_size.get()), self.entry_marker_color.get())
            if image_sam_points is not None:
                image.paste(image_sam_points, (0, 0), image_sam_points)
            image_contours = self.contours.to_overlay(dims[0], dims[1], self.entry_annotation_color.get())
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)

        filename = self.save_image_file('Save image', self.session.last_image_dir)
        if filename is not None:
            self.session.last_image_dir = os.path.dirname(filename)
            image.save(filename)
            self.log("Image saved to: %s" % filename)
            annotations = self.contours.to_opex(dims[0], dims[1])
            if annotations is not None:
                filename = os.path.splitext(filename)[0] + ".json"
                annotations.save_json_to_file(filename)
                self.log("Annotations saved to: %s" % filename)

    def on_file_close_click(self, event=None):
        self.state_to_session()
        self.session.save()
        self.mainwindow.quit()

    def on_autodetect_channels_click(self):
        self.session.autodetect_channels = (self.state_autodetect_channels.get() == 1)

    def on_keep_aspectratio_click(self):
        self.session.keep_aspectratio = (self.state_keep_aspectratio.get() == 1)
        self.update_image()

    def on_check_scan_dimensions_click(self):
        self.session.check_scan_dimensions = (self.state_check_scan_dimensions.get() == 1)

    def on_scale_r_changed(self, event):
        self.red_scale_value.configure(text=self.scale_to_text(self.state_scale_r.get()))
        self.session.scale_r = self.state_scale_r.get()
        self.update_image()

    def on_scale_g_changed(self, event):
        self.green_scale_value.configure(text=self.scale_to_text(self.state_scale_g.get()))
        self.session.scale_g = self.state_scale_g.get()
        self.update_image()

    def on_scale_b_changed(self, event):
        self.blue_scale_value.configure(text=self.scale_to_text(self.state_scale_b.get()))
        self.session.scale_b = self.state_scale_b.get()
        self.update_image()

    def on_window_resize(self, event):
        self.resize_image_label()

    def on_image_click(self, event=None):
        # modifiers: https://tkdocs.com/shipman/event-handlers.html
        state = event.state
        # remove NUMLOCK
        state &= ~0x0010
        # remove CAPSLOCK
        state &= ~0x0002
        # no modifier -> add
        if state == 0x0000:
            self.add_marker(event)
        # shift -> set label
        elif state == 0x0001:
            self.set_label(event)
        # ctrl -> clear
        elif state == 0x0004:
            self.clear_markers()

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
        if self.contours.has_contours() or self.markers.has_points():
            self.contours.clear()
            self.markers.clear()
            self.update_image()
            self.log("Annotations/marker points cleared")
        else:
            self.log("No annotations/marker points to clear")

    def on_tools_clear_markers_click(self, event=None):
        if self.markers.has_points():
            self.markers.clear()
            self.update_image()
            self.log("Marker points cleared")
        else:
            self.log("No marker points to clear")

    def on_tools_remove_last_annotations_click(self, event=None):
        if self.contours.remove_last():
            self.update_image()
            self.log("Last annotation removed")
        else:
            self.log("No annotations to remove")

    def on_sam_predictions(self, contours, meta):
        """
        Gets called when predictions become available.

        :param contours: the predicted (normalized) contours (list of list of x/y tuples)
        :type contours: list
        :param meta: meta-data of the predictions
        :type meta: dict
        """
        # add contours
        self.contours.add([Contour(points=x, meta=copy.copy(meta)) for x in contours])
        # update contours/image
        self.resize_image_label()

    def on_tools_sam_click(self, event=None):
        if not self.sam.is_connected():
            messagebox.showerror("Error", "Not connected to Redis server, cannot communicate with SAM!")
            self.notebook.select(2)
            return
        if not self.markers.has_points():
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

        # image as bytes
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        content = buf.getvalue()

        # absolute marker points
        points = self.markers.to_absolute(self.image_label.winfo_width(), self.image_label.winfo_height())
        self.markers.clear()

        # predict contours
        self.sam.predict(content, points,
                         self.state_redis_in.get(), self.state_redis_out.get(),
                         self.state_min_obj_size.get(), self.log, self.on_sam_predictions)

    def on_tools_polygon_click(self, event=None):
        if not self.markers.has_polygon():
            messagebox.showerror("Error", "At least three marker points necessary to create a polygon!")
            return

        self.contours.add([Contour(points=self.markers.points[:])])
        self.markers.clear()
        self.log("Polygon added")
        self.update_image()

    def on_tools_view_spectra_click(self, event=None):
        if not self.markers.has_points():
            messagebox.showerror("Error", "No marker points present!")
            return

        points = self.markers.to_spectra(self.data.scan_data)
        x = [x for x in range(self.data.get_num_bands())]
        plt.close()
        for p in points:
            plt.plot(x, points[p], label=p)
        plt.xlabel("band index")
        plt.ylabel("amplitude")
        plt.title("Spectra")
        plt.legend()
        plt.show()

    def on_metadata_clear_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        self.contours.clear_metadata()
        self.log("Meta-data cleared")

    def on_metadata_set_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        k = ttkSimpleDialog.askstring(
            title="Meta-data",
            prompt="Please enter the name of the meta-data value to set:",
            parent=self.mainwindow)
        if (k is None) or (k == ""):
            return
        v = ttkSimpleDialog.askstring(
            title="Meta-data",
            prompt="Please enter the value to set under '%s':" % k,
            parent=self.mainwindow)
        if (v is None) or (v == ""):
            return
        self.contours.set_metadata(k, v)
        self.log("Meta-data set: %s=%s" % (k, v))
        self.log("Meta-data:\n%s" % json.dumps(self.contours.metadata))

    def on_metadata_remove_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        k = ttkSimpleDialog.askstring(
            title="Meta-data",
            prompt="Please enter the name of the meta-data value to remove:",
            parent=self.mainwindow)
        if (k is None) or (k == ""):
            return
        msg = self.contours.remove_metadata(k)
        if msg is not None:
            messagebox.showwarning("Meta-data", msg)
        else:
            self.log("Meta-data:\n%s" % json.dumps(self.contours.metadata))

    def on_metadata_view_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        if self.contours.has_metadata():
            messagebox.showinfo("Meta-data", "Currently no meta-data stored.")
            return
        s = ""
        for k in self.contours.metadata:
            s += "%s:\n  %s\n" % (k, self.contours.metadata[k])
        self.log("Meta-data:\n%s" % json.dumps(self.contours.metadata))
        messagebox.showinfo("Meta-data", "Current meta-data:\n\n%s" % s)

    def on_button_sam_connect_click(self, event=None):
        if self.sam.is_connected():
            self.log("Disconnecting SAM...")
            self.button_sam_connect.configure(text="Connect")
            self.sam.disconnect()
            self.label_redis_connection.configure(text="Disconnected")
        else:
            self.log("Connecting SAM...")
            if self.sam.connect(host=self.state_redis_host.get(), port=self.state_redis_port.get(), pw=self.state_redis_pw.get()):
                self.label_redis_connection.configure(text="Connected")
                self.button_sam_connect.configure(text="Disconnect")
            else:
                self.label_redis_connection.configure(text="Failed to connect")

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
        prog="happy-envi-viewer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", "--scan", type=str, help="Path to the scan file (ENVI format)", required=False)
    parser.add_argument("-f", "--black_reference", type=str, help="Path to the black reference file (ENVI format)", required=False)
    parser.add_argument("-w", "--white_reference", type=str, help="Path to the white reference file (ENVI format)", required=False)
    parser.add_argument("-r", "--scale_r", metavar="INT", help="the wave length to use for the red channel", default=None, type=int, required=False)
    parser.add_argument("-g", "--scale_g", metavar="INT", help="the wave length to use for the green channel", default=None, type=int, required=False)
    parser.add_argument("-b", "--scale_b", metavar="INT", help="the wave length to use for the blue channel", default=None, type=int, required=False)
    parser.add_argument("--autodetect_channels", action="store_true", help="whether to determine the channels from the meta-data (overrides the manually specified channels)", required=False, default=None)
    parser.add_argument("--keep_aspectratio", action="store_true", help="whether to keep the aspect ratio", required=False, default=None)
    parser.add_argument("--check_scan_dimensions", action="store_true", help="whether to compare the dimensions of subsequently loaded scans and output a warning if they differ", required=False, default=None)
    parser.add_argument("--annotation_color", metavar="HEXCOLOR", help="the color to use for the annotations like contours (hex color)", default=None, required=False)
    parser.add_argument("--redis_host", metavar="HOST", type=str, help="The Redis host to connect to (IP or hostname)", default=None, required=False)
    parser.add_argument("--redis_port", metavar="PORT", type=int, help="The port the Redis server is listening on", default=None, required=False)
    parser.add_argument("--redis_pw", metavar="PASSWORD", type=str, help="The password to use with the Redis server", default=None, required=False)
    parser.add_argument("--redis_in", metavar="CHANNEL", type=str, help="The channel that SAM is receiving images on", default=None, required=False)
    parser.add_argument("--redis_out", metavar="CHANNEL", type=str, help="The channel that SAM is broadcasting the detections on", default=None, required=False)
    parser.add_argument("--redis_connect", action="store_true", help="whether to immediately connect to the Redis host", required=False, default=None)
    parser.add_argument("--marker_size", metavar="INT", help="The size in pixels for the SAM points", default=None, type=int, required=False)
    parser.add_argument("--marker_color", metavar="HEXCOLOR", help="the color to use for the SAM points (hex color)", default=None, required=False)
    parser.add_argument("--min_obj_size", metavar="INT", help="The minimum size that SAM contours need to have (<= 0 for no minimum)", default=None, type=int, required=False)
    parsed = parser.parse_args(args=args)
    app = ViewerApp()

    # override session data
    app.session.load()
    for p in PROPERTIES:
        if hasattr(parsed, p):
            value = getattr(parsed, p)
            if value is not None:
                setattr(app.session, p, value)
    app.session_to_state()

    if not app.session.autodetect_channels:
        app.set_wavelengths(app.session.scale_r, app.session.scale_g, app.session.scale_b)
    app.set_redis_connection(app.session.redis_host, app.session.redis_port, app.session.redis_pw, app.session.redis_in, app.session.redis_out)
    if app.session.redis_connect:
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
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    main()
