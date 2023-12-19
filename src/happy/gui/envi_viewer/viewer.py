#!/usr/bin/python3
import argparse
import copy
import io
import json
import logging
import matplotlib.pyplot as plt
import os
import pathlib
import pygubu
import traceback
import tkinter as tk
import tkinter.ttk as ttk

from datetime import datetime
from PIL import ImageTk, Image
from tkinter import filedialog as fd
from tkinter import messagebox
from ttkSimpleDialog import ttkSimpleDialog
from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data.black_ref import AbstractBlackReferenceMethod
from happy.data.white_ref import AbstractWhiteReferenceMethod
from happy.data.normalization import AbstractNormalization, SimpleNormalization
from happy.data import LABEL_WHITEREF, LABEL_BLACKREF
from happy.data.ref_locator import AbstractReferenceLocator
from happy.preprocessors import Preprocessor
from happy.data import DataManager, CALC_DIMENSIONS_DIFFER
from happy.data.annotations import ContoursManager, Contour
from happy.data.annotations import MarkersManager
from happy.gui.envi_viewer import SamManager
from happy.gui.envi_viewer import SessionManager, PROPERTIES
from happy.gui.dialog import asklist
from happy.gui.envi_viewer.annotations import AnnotationsDialog
from happy.gui import UndoManager
from opex import ObjectPredictions

PROG = "happy-envi-viewer"

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "viewer.ui"

DIMENSIONS = "H: %d, W: %d, C: %d"

logger = logging.getLogger(PROG)

LOG_TIMESTAMP_FORMAT = "[%H:%M:%S.%f]"


class ViewerApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # Main widget
        self.mainwindow = builder.get_object("toplevel", master)
        builder.connect_callbacks(self)
        self.mainwindow.iconphoto(False, tk.PhotoImage(file=str(PROJECT_PATH) + '/../../logo.png'))
        self.mainwindow.bind("<Configure>", self.on_window_resize)

        # setting theme
        style = ttk.Style(self.mainwindow)
        style.theme_use('clam')

        # attach variables to app itself
        self.state_keep_aspectratio = None
        self.state_autodetect_channels = None
        self.state_check_scan_dimensions = None
        self.state_export_to_scan_dir = None
        self.state_annotation_color = None
        self.state_predefined_labels = None
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
        self.state_export_overlay_annotations = None
        self.state_export_keep_aspectratio = None
        self.state_black_ref_locator = None
        self.state_black_ref_method = None
        self.state_white_ref_locator = None
        self.state_white_ref_method = None
        self.state_normalization = None
        builder.import_variables(self)

        # reference components
        self.notebook = builder.get_object("notebook", master)
        # image
        self.frame_image = builder.get_object("frame_image", master)
        self.image_canvas = builder.get_object("canvas_image", master)
        color = ttk.Style().lookup("TFrame", "background", default="white")
        self.image_canvas.configure(background=color)
        self.scrollbarhelper_canvas = builder.get_object("scrollbarhelper_canvas", master)
        # info
        self.text_info = builder.get_object("text_info", master)
        # options
        self.checkbutton_autodetect_channels = builder.get_object("checkbutton_autodetect_channels", master)
        self.checkbutton_keep_aspectratio = builder.get_object("checkbutton_keep_aspectratio", master)
        self.checkbutton_check_scan_dimenions = builder.get_object("checkbutton_check_scan_dimensions", master)
        self.checkbutton_export_to_scan_dir = builder.get_object("checkbutton_export_to_scan_dir", master)
        self.entry_annotation_color = builder.get_object("entry_annotation_color", master)
        self.entry_predefined_labels = builder.get_object("entry_predefined_labels", master)
        self.entry_redis_host = builder.get_object("entry_redis_host", master)
        self.entry_redis_port = builder.get_object("entry_redis_port", master)
        self.entry_redis_in = builder.get_object("entry_redis_in", master)
        self.entry_redis_out = builder.get_object("entry_redis_out", master)
        self.entry_marker_size = builder.get_object("entry_marker_size", master)
        self.entry_marker_color = builder.get_object("entry_marker_color", master)
        self.entry_min_obj_size = builder.get_object("entry_min_obj_size", master)
        self.label_redis_connection = builder.get_object("label_redis_connection", master)
        self.button_sam_connect = builder.get_object("button_sam_connect", master)
        self.entry_black_ref_locator = builder.get_object("entry_black_ref_locator", master)
        self.entry_black_ref_method = builder.get_object("entry_black_ref_method", master)
        self.entry_white_ref_locator = builder.get_object("entry_white_ref_locator", master)
        self.entry_white_ref_method = builder.get_object("entry_white_ref_method", master)
        self.text_preprocessing = builder.get_object("text_preprocessing", master)
        self.entry_normalization = builder.get_object("entry_normalization", master)
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
        self.label_calc_norm_data = builder.get_object("label_calc_norm_data", master)

        # accelerators are just strings, we need to bind them to actual methods
        # https://tkinterexamples.com/events/keyboard/
        self.mainwindow.bind("<Control-o>", self.on_file_open_scan_click)
        self.mainwindow.bind("<Control-n>", self.on_file_clear_blackref)
        self.mainwindow.bind("<Control-r>", self.on_file_open_blackref)
        self.mainwindow.bind("<Control-N>", self.on_file_clear_whiteref)  # upper case N implies Shift key!
        self.mainwindow.bind("<Control-R>", self.on_file_open_whiteref)   # upper case R implies Shift key!
        self.mainwindow.bind("<Control-e>", self.on_file_exportimage_click)
        self.mainwindow.bind("<Alt-x>", self.on_file_close_click)
        self.mainwindow.bind("<Control-A>", self.on_edit_clear_annotations_click)
        self.mainwindow.bind("<Alt-e>", self.on_edit_edit_annotations_click)
        self.mainwindow.bind("<Control-z>", self.on_edit_undo_click)
        self.mainwindow.bind("<Control-y>", self.on_edit_redo_click)
        self.mainwindow.bind("<Control-M>", self.on_edit_clear_markers_click)
        self.mainwindow.bind("<Control-L>", self.on_edit_remove_last_annotations_click)
        self.mainwindow.bind("<Control-s>", self.on_tools_sam_click)
        self.mainwindow.bind("<Control-p>", self.on_tools_polygon_click)
        self.mainwindow.bind("<Control-w>", self.on_tools_view_spectra_click)
        self.mainwindow.bind("<Control-W>", self.on_tools_view_spectra_processed_click)

        # mouse events
        # https://tkinterexamples.com/events/mouse/
        self.image_canvas.bind("<Button-1>", self.on_image_click)
        self.label_r_value.bind("<Button-1>", self.on_label_r_click)
        self.label_g_value.bind("<Button-1>", self.on_label_g_click)
        self.label_b_value.bind("<Button-1>", self.on_label_b_click)

        # init some vars
        self.photo_scan = None
        self.session = SessionManager(log_method=self.log)
        self.contours = ContoursManager()
        self.data = DataManager(contours=self.contours, log_method=self.log)
        self.last_dims = None
        self.last_wavelengths = None
        self.markers = MarkersManager()
        self.sam = SamManager()
        self.spectra_plot_raw = None
        self.spectra_plot_processed = None
        self.ignore_updates = False
        self.undo_manager = UndoManager(log_method=self.log)

    def run(self):
        self.mainwindow.mainloop()

    def log(self, msg):
        """
        Prints message on stdout.

        :param msg: the message to log
        :type msg: str
        """
        if msg != "":
            logger.info(msg)
            if hasattr(self, "text_log") and (self.text_log is not None):
                self.text_log.insert(tk.END, "\n" + datetime.now().strftime(LOG_TIMESTAMP_FORMAT) + " " + msg)

    def start_busy(self):
        """
        Displays the hourglass cursor.
        https://www.tcl.tk/man/tcl8.4/TkCmd/cursors.html
        """
        self.mainwindow.config(cursor="watch")
        self.mainwindow.update()

    def stop_busy(self):
        """
        Displays the normal cursor.
        """
        self.mainwindow.config(cursor="")
        self.mainwindow.update()

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
        if isinstance(filename, tuple):
            filename = None

        return filename

    def open_opex_file(self, title, initial_dir):
        """
        Allows the user to select an OPEX JSON annotation file.

        :param title: the title for the open dialog
        :type title: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        filetypes = (
            ('OPEX JSON files', '*.json'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=filetypes)
        if filename == "":
            filename = None
        if isinstance(filename, tuple):
            filename = None

        return filename

    def save_image_file(self, title, initial_dir, scan=None):
        """
        Allows the user to select a PNG file for saving an image.
         
        :param title: the title to use for the save dialog
        :type title: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :param scan: the scan image to use for a suggestion
        :type scan: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        filetypes = (
            ('PNG files', '*.png'),
            ('All files', '*.*')
        )

        initial_file = None
        if scan is not None:
            initial_file = os.path.splitext(os.path.basename(scan))[0] + ".png"

        filename = fd.asksaveasfilename(
            title=title,
            initialdir=initial_dir,
            initialfile=initial_file,
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
            self.last_wavelengths = copy.copy(self.data.get_wavelengths())

        self.log("Loading scan: %s" % filename)
        self.session.last_scan_file = filename
        self.start_busy()
        warning = self.data.set_scan(filename)
        self.stop_busy()
        if warning is not None:
            messagebox.showerror("Warning", warning)

        # different dimensions?
        if self.session.check_scan_dimensions:
            if (self.last_dims is not None) and (self.data.has_scan()):
                if self.last_dims != self.data.scan_data.shape:
                    warning = "Different data dimensions detected: last=%s, new=%s" % (str(self.last_dims), str(self.data.scan_data.shape))
                    messagebox.showwarning("Different dimensions", warning)
                elif self.last_wavelengths != self.data.get_wavelengths():
                    self.log("Last wavelengths: %s" % str(self.last_wavelengths))
                    self.log("Current wavelengths: %s" % str(self.data.get_wavelengths()))
                    messagebox.showwarning("Different wavelengths", "Different wavelengths detected (see console for last/current)!")

        # configure scales
        self.set_data_dimensions(self.data.scan_data.shape, do_update=False)

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
        self.start_busy()
        error = self.data.set_blackref(filename)
        self.stop_busy()
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
        self.start_busy()
        error = self.data.set_whiteref(filename)
        self.stop_busy()
        if error is not None:
            messagebox.showerror("Error", error)
            return
        if do_update:
            self.update()

    def set_data_dimensions(self, dimensions, do_update=False):
        """
        Updates the sliders and dimensions display.

        :param dimensions: the dimensions of the data (height,width,bands)
        :param do_update: whether to update the image
        :type do_update: bool
        """
        self.ignore_updates = True

        num_bands = dimensions[2]
        r = self.state_scale_r.get()
        g = self.state_scale_g.get()
        b = self.state_scale_b.get()
        self.red_scale.configure(to=num_bands - 1)
        self.green_scale.configure(to=num_bands - 1)
        self.blue_scale.configure(to=num_bands - 1)
        if r >= num_bands:
            self.red_scale.set(num_bands - 1)
        if g >= num_bands:
            self.red_scale.set(num_bands - 1)
        if b >= num_bands:
            self.red_scale.set(num_bands - 1)
        self.label_dims.configure(text=DIMENSIONS % dimensions)

        self.ignore_updates = False
        if do_update:
            self.update_image()

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

    def get_image_canvas_dims(self):
        """
        Returns the dimensions of the image label displaying the data.

        :return: the tuple (w,h) of the image label, None if no data
        :rtype: tuple
        """
        if self.data.norm_data is None:
            return None
        else:
            return self.frame_image.winfo_width() - 10, self.frame_image.winfo_height() - 10

    def fit_image_into_dims(self, available_width, available_height, keep_aspectratio):
        """
        Fits the image into the specified available dimensions and returns the calculated dimensions.

        :param available_width: the width to scale to, skips calculation if 0 or less
        :type available_width: int
        :param available_height: the height to scale to
        :type available_height: int
        :param keep_aspectratio: whether to keep the aspect ratio
        :type keep_aspectratio: bool
        :return: the scaled dimensions (w,h), None if invalid width/height
        :rtype: tuple
        """
        if available_width < 1:
            return None
        if available_height < 1:
            return None

        # keep aspect ratio?
        if keep_aspectratio:
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

    def resize_image_canvas(self):
        """
        Computes the scaled image and updates the GUI.
        """
        if not self.data.has_scan():
            return

        if self.session.zoom < 0:
            dims = self.get_image_canvas_dims()
            if dims is not None:
                dims = self.fit_image_into_dims(dims[0], dims[1], self.session.keep_aspectratio)
        else:
            if self.session.keep_aspectratio:
                dims = (self.data.scan_data.shape[1], self.data.scan_data.shape[0])
                dims = (int(dims[0] * self.session.zoom / 100), int(dims[1] * self.session.zoom / 100))
            else:
                dims = self.get_image_canvas_dims()
                if dims is not None:
                    canvas_ratio = dims[0] / dims[1]
                    image_ratio = self.data.scan_data.shape[1] / self.data.scan_data.shape[0]
                    dims = (dims[0] / image_ratio * canvas_ratio, dims[1] / image_ratio * canvas_ratio)
                    dims = (int(dims[0] * self.session.zoom / 100), int(dims[1] * self.session.zoom / 100))

        if dims is None:
            return

        width = dims[0]
        height = dims[1]
        image = self.get_scaled_image(width, height)
        if image is not None:
            image_markers = self.markers.to_overlay(width, height, int(self.entry_marker_size.get()), self.entry_marker_color.get())
            if image_markers is not None:
                image.paste(image_markers, (0, 0), image_markers)
            image_contours = self.contours.to_overlay(width, height, self.entry_annotation_color.get())
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)
            self.photo_scan = ImageTk.PhotoImage(image=image)
            self.image_canvas.create_image(0, 0, image=self.photo_scan, anchor=tk.NW)
            self.image_canvas.config(width=width, height=height)
            self.image_canvas.configure(scrollregion=(0, 0, width - 2, height - 2))

    def update_image(self):
        """
        Updates the image.
        """
        if self.ignore_updates:
            return
        success = self.data.update_image(int(self.red_scale.get()), int(self.green_scale.get()), int(self.blue_scale.get()))
        if (CALC_DIMENSIONS_DIFFER in success) and success[CALC_DIMENSIONS_DIFFER]:
            self.set_data_dimensions(self.data.norm_data.shape, do_update=False)
        # make visible in UI
        if len(success) > 0:
            self.label_calc_norm_data["text"] = self.data.calc_norm_data_indicator(success)
            self.log("calc_norm_data steps: " + str(success))
        self.resize_image_canvas()
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
        if self.data.whiteref_file is not None:
            info += self.data.whiteref_file + "\n" + str(self.data.whiteref_data.shape)
        else:
            contours = self.contours.get_contours(LABEL_WHITEREF)
            if len(contours) == 1:
                info += str(contours[0].bbox())
            else:
                info += "-none-"
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
        if self.ignore_updates:
            return
        self.start_busy()
        self.update_image()
        self.update_info()
        self.stop_busy()

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
        self.undo_manager.add_undo("Adding marker", self.get_undo_state())
        x = self.image_canvas.canvasx(event.x) / self.photo_scan.width()
        y = self.image_canvas.canvasy(event.y) / self.photo_scan.height()
        point = (x, y)
        self.markers.add(point)
        self.log("Marker point added: %s" % str(point))
        self.update_image()

    def get_predefined_labels(self):
        """
        Returns the list of predefined labels (if any).

        :return: the list of labels or None if not defined
        :rtype: list
        """
        if len(self.state_predefined_labels.get()) > 0:
            result = [x.strip() for x in self.state_predefined_labels.get().split(",")]
            if "" not in result:
                result.insert(0, "")
            return result
        else:
            return None

    def set_label(self, event):
        """
        Prompts the user to enter a label for the contours that contain the event's position.

        :param event: the event that triggered the label setting
        """
        x = self.image_canvas.canvasx(event.x) / self.photo_scan.width()
        y = self.image_canvas.canvasy(event.y) / self.photo_scan.height()
        contours = self.contours.contains(x, y)
        if len(contours) > 0:
            labels = set([x.label for x in contours])
            if len(contours) > 1:
                text = "Please enter the label to apply to %d contours:" % len(contours)
            else:
                text = "Please enter the label"
            items = self.get_predefined_labels()
            if items is not None:
                label = "" if (len(labels) != 1) else list(labels)[0]
                if label not in items:
                    label = ""
                new_label = asklist(
                    title="Object label",
                    prompt=text,
                    items=items,
                    initialvalue=label,
                    parent=self.mainwindow)
            else:
                new_label = ttkSimpleDialog.askstring(
                    title="Object label",
                    prompt=text,
                    initialvalue="" if (len(labels) != 1) else list(labels)[0],
                    parent=self.mainwindow)
            if new_label is not None:
                for contour in contours:
                    contour.label = new_label
                if (new_label == LABEL_WHITEREF) or (new_label == LABEL_BLACKREF):
                    self.data.reset_norm_data()
                self.update_info()
                self.update_image()

    def clear_markers(self):
        """
        Clears all markers.
        """
        self.markers.clear()
        self.log("Marker points cleared")

    def remove_annotations(self, event):
        """
        Removes annotations that the click position covers.
        """
        x = self.image_canvas.canvasx(event.x) / self.photo_scan.width()
        y = self.image_canvas.canvasy(event.y) / self.photo_scan.height()
        contours = self.contours.contains(x, y)
        if len(contours) > 0:
            answer = messagebox.askquestion("Remove annotations", "Remove %d annotations?" % len(contours))
            if answer == messagebox.YES:
                self.contours.remove(contours)
            self.update_image()

    def state_to_session(self):
        """
        Transfers the current state in the UI to the session manager.
        """
        self.session.autodetect_channels = (self.state_autodetect_channels.get() == 1)
        self.session.keep_aspectratio = (self.state_keep_aspectratio.get() == 1)
        self.session.check_scan_dimensions = (self.state_check_scan_dimensions.get() == 1)
        self.session.export_to_scan_dir = (self.state_export_to_scan_dir.get() == 1)
        # last_blackref_dir
        # last_whiteref_dir
        # last_scan_dir
        # last_image_dir
        # last_session_dir
        self.session.scale_r = self.state_scale_r.get()
        self.session.scale_g = self.state_scale_g.get()
        self.session.scale_b = self.state_scale_b.get()
        self.session.annotation_color = self.state_annotation_color.get()
        self.session.predefined_labels = self.state_predefined_labels.get()
        self.session.redis_host = self.state_redis_host.get()
        self.session.redis_port = self.state_redis_port.get()
        self.session.redis_pw = self.state_redis_pw.get()
        self.session.redis_in = self.state_redis_in.get()
        self.session.redis_out = self.state_redis_out.get()
        self.session.marker_size = self.state_marker_size.get()
        self.session.marker_color = self.state_marker_color.get()
        self.session.min_obj_size = self.state_min_obj_size.get()
        self.session.black_ref_locator = self.state_black_ref_locator.get()
        self.session.black_ref_method = self.state_black_ref_method.get()
        self.session.white_ref_locator = self.state_white_ref_locator.get()
        self.session.white_ref_method = self.state_white_ref_method.get()
        self.session.preprocessing = self.text_preprocessing.get("1.0", "end-1c")
        self.session.export_overlay_annotations = self.state_export_overlay_annotations.get() == 1
        self.session.export_keep_aspectratio = self.state_export_keep_aspectratio.get() == 1
        # zoom
        self.session.normalization = self.state_normalization.get()

    def session_to_state(self):
        """
        Transfers the session data to the UI.
        """
        self.state_autodetect_channels.set(1 if self.session.autodetect_channels else 0)
        self.state_keep_aspectratio.set(1 if self.session.keep_aspectratio else 0)
        self.state_check_scan_dimensions.set(1 if self.session.check_scan_dimensions else 0)
        self.state_export_to_scan_dir.set(1 if self.session.export_to_scan_dir else 0)
        # last_blackref_dir
        # last_whiteref_dir
        # last_scan_dir
        # last_image_dir
        # last_session_dir
        self.state_scale_r.set(self.session.scale_r)
        self.state_scale_g.set(self.session.scale_g)
        self.state_scale_b.set(self.session.scale_b)
        self.state_annotation_color.set(self.session.annotation_color)
        self.state_predefined_labels.set(self.session.predefined_labels)
        self.state_redis_host.set(self.session.redis_host)
        self.state_redis_port.set(self.session.redis_port)
        self.state_redis_pw.set(self.session.redis_pw)
        self.state_redis_in.set(self.session.redis_in)
        self.state_redis_out.set(self.session.redis_out)
        self.state_marker_size.set(self.session.marker_size)
        self.state_marker_color.set(self.session.marker_color)
        self.state_min_obj_size.set(self.session.min_obj_size)
        self.state_black_ref_locator.set(self.session.black_ref_locator)
        self.state_black_ref_method.set(self.session.black_ref_method)
        self.state_white_ref_locator.set(self.session.white_ref_locator)
        self.state_white_ref_method.set(self.session.white_ref_method)
        self.text_preprocessing.delete(1.0, tk.END)
        self.text_preprocessing.insert(tk.END, self.session.preprocessing)
        self.state_export_overlay_annotations.set(1 if self.session.export_overlay_annotations else 0)
        self.state_export_keep_aspectratio.set(1 if self.session.export_keep_aspectratio else 0)
        # zoom
        self.state_normalization.set(self.session.normalization)

        # activate
        self.apply_black_ref(do_update=False)
        self.apply_white_ref(do_update=False)
        self.apply_preprocessing(do_update=False)

    def get_undo_state(self):
        """
        Returns the state of the annotations as dictionary.

        :return: the dictionary
        :rtype: dict
        """
        return {
            "markers": self.markers.to_json(),
            "contours": self.contours.to_json(),
        }

    def restore_undo_state(self, d):
        """
        Restores the state of the annotations from the dictionary.

        :param d: the state dictionary
        :type d: dict
        """
        self.markers.from_json(d["markers"])
        self.contours.from_json(d["contours"])

    def apply_black_ref(self, do_update=False):
        # locator
        cmdline = self.state_black_ref_locator.get()
        try:
            loc = AbstractReferenceLocator.parse_locator(cmdline)
            self.data.set_blackref_locator(loc)
            self.session.black_ref_locator = cmdline
            self.log("Setting black ref locator: %s" % cmdline)
        except:
            messagebox.showerror("Error", "Failed to parse reference locator: %s" % cmdline)
            return False
        # method
        cmdline = self.state_black_ref_method.get()
        try:
            method = AbstractBlackReferenceMethod.parse_method(cmdline)
            self.data.set_blackref_method(method)
            self.session.black_ref_method = cmdline
            self.log("Setting black ref method: %s" % cmdline)
        except:
            messagebox.showerror("Error", "Failed to parse black reference method: %s" % cmdline)
            return False
        if do_update:
            self.update_image()
        return True

    def apply_white_ref(self, do_update=False):
        # locator
        cmdline = self.state_white_ref_locator.get()
        try:
            loc = AbstractReferenceLocator.parse_locator(cmdline)
            self.data.set_whiteref_locator(loc)
            self.session.white_ref_locator = cmdline
            self.log("Setting white ref locator: %s" % cmdline)
        except:
            messagebox.showerror("Error", "Failed to parse reference locator: %s" % cmdline)
            return False
        # method
        cmdline = self.state_white_ref_method.get()
        try:
            method = AbstractWhiteReferenceMethod.parse_method(cmdline)
            self.data.set_whiteref_method(method)
            self.session.white_ref_method = cmdline
            self.log("Setting white ref method: %s" % cmdline)
        except:
            messagebox.showerror("Error", "Failed to parse white reference method: %s" % cmdline)
            return False
        if do_update:
            self.update_image()
        return True

    def apply_preprocessing(self, do_update=False):
        cmdline = self.text_preprocessing.get("1.0", "end-1c")
        if len(cmdline.strip()) > 0:
            try:
                preprocs = Preprocessor.parse_preprocessors(cmdline)
                self.data.set_preprocessors(preprocs)
                self.log("Setting preprocessing: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse preprocessing: %s" % cmdline)
                return False
        else:
            self.data.set_preprocessors([])
            self.log("Removing preprocessing")
        if do_update:
            self.update_image()
        return True

    def apply_normalization(self, do_update=False):
        cmdline = self.entry_normalization.get()
        if len(cmdline.strip()) > 0:
            try:
                norm = AbstractNormalization.parse_normalization(cmdline)
                self.data.set_normalization(norm)
                self.log("Setting normalization: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse normalization: %s" % cmdline)
                return False
        else:
            self.data.set_normalization(None)
            self.log("Removing normalization")
        if do_update:
            self.update_image()
        return True

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
            self.undo_manager.clear()

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

    def on_file_importannotations_click(self, event=None):
        """
        Allows the user to select a JSON file for loading OPEX annotations from.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_opex_file('Open OPEX JSON annotations', self.session.last_scan_dir)

        if filename is not None:
            preds = ObjectPredictions.load_json_from_file(filename)
            if len(self.state_predefined_labels.get()) > 0:
                pre_labels = [x.strip() for x in self.state_predefined_labels.get().split(",")]
                cur_labels = [x.label for x in preds.objects]
                missing_labels = set()
                for cur_label in cur_labels:
                    if cur_label not in pre_labels:
                        missing_labels.add(cur_label)
                if len(missing_labels) > 0:
                    missing_labels = sorted(list(missing_labels))
                    messagebox.showwarning(
                        "Warning",
                        "The following labels from the imported annotations are not listed under the predefined labels:\n" + ",".join(missing_labels))
            self.undo_manager.add_undo("Importing annotations", self.get_undo_state())
            self.contours.from_opex(preds, self.data.scan_data.shape[1], self.data.scan_data.shape[0])
            self.update_image()

    def on_file_exportimage_click(self, event=None):
        """
        Allows the user to select a PNG file for saving the false color RGB to.
        """
        if self.session.export_keep_aspectratio:
            dims = self.data.dims()
        else:
            dims = self.get_image_canvas_dims()
        if dims is None:
            return
        dims = self.fit_image_into_dims(dims[0], dims[1], self.session.export_keep_aspectratio)
        image = self.get_scaled_image(dims[0], dims[1])
        if image is None:
            return

        # include annotations?
        if self.session.export_overlay_annotations:
            image_sam_points = self.markers.to_overlay(dims[0], dims[1], int(self.entry_marker_size.get()), self.entry_marker_color.get())
            if image_sam_points is not None:
                image.paste(image_sam_points, (0, 0), image_sam_points)
            image_contours = self.contours.to_overlay(dims[0], dims[1], self.entry_annotation_color.get())
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)

        if self.session.export_to_scan_dir:
            initial_dir = os.path.dirname(self.data.scan_file)
        else:
            initial_dir = self.session.last_image_dir
        filename = self.save_image_file('Save image', initial_dir, scan=self.session.last_scan_file)
        if filename is not None:
            self.session.last_image_dir = os.path.dirname(filename)
            image.save(filename)
            self.log("Image saved to: %s" % filename)
            annotations = self.contours.to_opex(dims[0], dims[1])
            if annotations is not None:
                filename = os.path.splitext(filename)[0] + ".json"
                annotations.save_json_to_file(filename)
                self.log("Annotations saved to: %s" % filename)

    def on_export_overlay_annotations(self, event=None):
        self.session.export_overlay_annotations = self.state_export_overlay_annotations.get() == 1

    def on_export_keep_aspectratio(self, event=None):
        self.session.export_keep_aspectratio = self.state_export_keep_aspectratio.get() == 1

    def on_file_session_open(self, event=None):
        """
        Lets the user restore a session file.
        """
        filetypes = (
            ('Session files', '*.json'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(
            title="Open session",
            initialdir=self.session.last_session_dir,
            filetypes=filetypes)
        if filename == "":
            filename = None
        if isinstance(filename, tuple):
            filename = None
        if filename is not None:
            self.session.load(filename)
            self.session.last_session_dir = os.path.dirname(filename)
            self.session_to_state()
            self.update()

    def on_file_session_save(self, event=None):
        """
        Lets the user save a session to a file.
        """
        filetypes = (
            ('Session files', '*.json'),
            ('All files', '*.*')
        )
        initial_file = None
        filename = fd.asksaveasfilename(
            title="Save session",
            initialdir=self.session.last_session_dir,
            initialfile=initial_file,
            filetypes=filetypes)
        if filename == "":
            filename = None
        if filename is not None:
            self.state_to_session()
            self.session.last_session_dir = os.path.dirname(filename)
            self.session.save(filename)

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

    def on_export_to_scan_dir_click(self):
        self.session.export_to_scan_dir = (self.state_export_to_scan_dir.get() == 1)

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
        self.resize_image_canvas()

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
        # ctrl+shift -> remove annotation
        elif state == 0x0005:
            self.remove_annotations(event)

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

    def on_edit_undo_click(self, event=None):
        if self.undo_manager.can_undo():
            state = self.undo_manager.undo()
            self.undo_manager.add_redo(state.comment, self.get_undo_state())
            self.log("Undoing: %s" % state.comment)
            self.restore_undo_state(state.data)
            self.update_image()
        else:
            self.log("Nothing to undo!")

    def on_edit_redo_click(self, event=None):
        if self.undo_manager.can_redo():
            state = self.undo_manager.redo()
            self.undo_manager.add_undo(state.comment, self.get_undo_state())
            self.log("Redoing: %s" % state.comment)
            self.restore_undo_state(state.data)
            self.update_image()
        else:
            self.log("Nothing to redo!")

    def on_edit_clear_annotations_click(self, event=None):
        self.undo_manager.add_undo("Clearing annotations", self.get_undo_state())
        if self.contours.has_contours() or self.markers.has_points():
            self.contours.clear()
            self.markers.clear()
            self.update_image()
            self.log("Annotations/marker points cleared")
        else:
            self.log("No annotations/marker points to clear")

    def on_annotations_updated(self, changed, deleted):
        """
        Gets called when "edit annotations" dialog gets accepted.

        :param changed: the list of changed Contour objects
        :type changed: list
        :param deleted: the list of deleted Contour objects
        :type deleted: list
        """
        if (len(deleted) == 0) and (len(changed) == 0):
            return

        self.undo_manager.add_undo("Editing annotations", self.get_undo_state())
        if len(deleted) > 0:
            self.log("Removing %d annotations" % len(deleted))
            self.contours.remove(deleted)
        if len(changed) > 0:
            self.log("Updating labels for %d annotations" % len(changed))
            for c in changed:
                self.contours.update_label(c, c.label)
        self.update_image()

    def on_edit_edit_annotations_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if len(self.contours.contours) == 0:
            messagebox.showerror("Error", "Please add annotations first!")
            return

        dialog = AnnotationsDialog(self.mainwindow, self.contours,
                                   self.data.scan_data.shape[1], self.data.scan_data.shape[0],
                                   predefined_labels=self.get_predefined_labels())
        dialog.show(self.on_annotations_updated)

    def on_edit_clear_markers_click(self, event=None):
        self.undo_manager.add_undo("Clearing markers", self.get_undo_state())
        if self.markers.has_points():
            self.markers.clear()
            self.update_image()
            self.log("Marker points cleared")
        else:
            self.log("No marker points to clear")

    def on_edit_remove_last_annotations_click(self, event=None):
        self.undo_manager.add_undo("Removing last annotations", self.get_undo_state())
        if self.contours.remove_last():
            self.update_image()
            self.log("Last annotation removed")
        else:
            self.log("No annotations to remove")

    def on_edit_metadata_clear_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        self.undo_manager.add_undo("Clearing meta-data", self.get_undo_state())
        self.contours.clear_metadata()
        self.log("Meta-data cleared")

    def on_edit_metadata_set_click(self, event=None):
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
        self.undo_manager.add_undo("Editing meta-data", self.get_undo_state())
        self.contours.set_metadata(k, v)
        self.log("Meta-data set: %s=%s" % (k, v))
        self.log("Meta-data:\n%s" % json.dumps(self.contours.metadata))

    def on_edit_metadata_remove_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        k = ttkSimpleDialog.askstring(
            title="Meta-data",
            prompt="Please enter the name of the meta-data value to remove:",
            parent=self.mainwindow)
        if (k is None) or (k == ""):
            return
        self.undo_manager.add_undo("Removing meta-data", self.get_undo_state())
        msg = self.contours.remove_metadata(k)
        if msg is not None:
            messagebox.showwarning("Meta-data", msg)
        else:
            self.log("Meta-data:\n%s" % json.dumps(self.contours.metadata))

    def on_edit_metadata_view_click(self, event=None):
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

    def on_sam_predictions(self, contours, meta):
        """
        Gets called when predictions become available.

        :param contours: the predicted (normalized) contours (list of list of x/y tuples)
        :type contours: list
        :param meta: meta-data of the predictions
        :type meta: dict
        """
        self.undo_manager.add_undo("Adding SAM annotations", self.get_undo_state())
        # add contours
        self.contours.add([Contour(points=x, meta=copy.copy(meta)) for x in contours])
        # update contours/image
        self.resize_image_canvas()

    def on_tools_sam_click(self, event=None):
        if not self.sam.is_connected():
            messagebox.showerror("Error", "Not connected to Redis server, cannot communicate with SAM!")
            self.notebook.select(2)
            return
        if not self.markers.has_points():
            messagebox.showerror("Error", "No prompt points for SAM collected!")
            return

        # image
        dims = self.get_image_canvas_dims()
        if dims is None:
            messagebox.showerror("Error", "No image available!")
            return
        dims = self.fit_image_into_dims(dims[0], dims[1], self.session.keep_aspectratio)
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
        points = self.markers.to_absolute(self.image_canvas.winfo_width(), self.image_canvas.winfo_height())
        self.markers.clear()

        # predict contours
        self.sam.predict(content, points,
                         self.state_redis_in.get(), self.state_redis_out.get(),
                         self.state_min_obj_size.get(), self.log, self.on_sam_predictions)

    def on_button_black_ref_apply(self, event=None):
        self.apply_black_ref(do_update=True)

    def on_button_white_ref_apply(self, event=None):
        self.apply_white_ref(do_update=True)

    def on_button_preprocessing_apply(self, event=None):
        self.apply_preprocessing(do_update=True)

    def on_button_normalization_apply(self, event=None):
        self.apply_normalization(do_update=True)

    def on_tools_polygon_click(self, event=None):
        if not self.markers.has_polygon():
            messagebox.showerror("Error", "At least three marker points necessary to create a polygon!")
            return

        self.undo_manager.add_undo("Adding polygon", self.get_undo_state())
        self.contours.add([Contour(points=self.markers.points[:])])
        self.markers.clear()
        self.log("Polygon added")
        self.update_image()

    def on_tools_view_spectra_click(self, event=None):
        if not self.markers.has_points():
            messagebox.showerror("Error", "No marker points present!")
            return

        points = self.markers.to_spectra(self.data.scan_data)
        x = [x for x in range(self.data.get_num_bands_scan())]
        if self.spectra_plot_raw is not None:
            plt.close(self.spectra_plot_raw)
        self.spectra_plot_raw = plt.figure(num='ENVI Viewer: Spectra (raw)')
        for p in points:
            plt.plot(x, points[p], label=p)
        plt.xlabel("band index")
        plt.ylabel("amplitude")
        plt.title("Spectra")
        plt.legend()
        plt.show()

    def on_tools_view_spectra_processed_click(self, event=None):
        if not self.markers.has_points():
            messagebox.showerror("Error", "No marker points present!")
            return

        points = self.markers.to_spectra(self.data.norm_data)
        x = [x for x in range(self.data.get_num_bands_norm())]
        if self.spectra_plot_processed is not None:
            plt.close(self.spectra_plot_processed)
        self.spectra_plot_processed = plt.figure(num='ENVI Viewer: Spectra (processed)')
        for p in points:
            plt.plot(x, points[p], label=p)
        plt.xlabel("band index")
        plt.ylabel("amplitude")
        plt.title("Spectra")
        plt.legend()
        plt.show()

    def on_zoom_click(self, event=None):
        if (event is not None) and (event.startswith("command_zoom_")):
            try:
                zoom = int(event.replace("command_zoom_", ""))
                self.session.zoom = zoom
                self.update_image()
            except:
                self.log("Failed to extract zoom from: %s" % event)

    def on_zoom_fit(self, event=None):
        self.session.zoom = -1
        self.update_image()

    def on_zoom_custom(self, event=None):
        curr_zoom = self.session.zoom
        if curr_zoom <= 0:
            curr_zoom = -1
        new_zoom = ttkSimpleDialog.askinteger("Zoom", "Please enter new zoom (in %; -1 for best fit):", initialvalue=curr_zoom)
        if new_zoom is not None:
            if new_zoom <= 0:
                new_zoom = -1
            self.session.zoom = new_zoom
            self.update_image()

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
    init_app()
    parser = argparse.ArgumentParser(
        description="ENVI Hyperspectral Image Viewer.\nOffers contour detection using SAM (Segment-Anything: https://github.com/waikato-datamining/pytorch/tree/master/segment-anything)",
        prog=PROG,
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
    parser.add_argument("--export_to_scan_dir", action="store_true", help="whether to export images to the scan directory rather than the last one used", required=False, default=None)
    parser.add_argument("--annotation_color", metavar="HEXCOLOR", help="the color to use for the annotations like contours (hex color)", default=None, required=False)
    parser.add_argument("--predefined_labels", metavar="LIST", help="the comma-separated list of labels to use", default=None, required=False)
    parser.add_argument("--redis_host", metavar="HOST", type=str, help="The Redis host to connect to (IP or hostname)", default=None, required=False)
    parser.add_argument("--redis_port", metavar="PORT", type=int, help="The port the Redis server is listening on", default=None, required=False)
    parser.add_argument("--redis_pw", metavar="PASSWORD", type=str, help="The password to use with the Redis server", default=None, required=False)
    parser.add_argument("--redis_in", metavar="CHANNEL", type=str, help="The channel that SAM is receiving images on", default=None, required=False)
    parser.add_argument("--redis_out", metavar="CHANNEL", type=str, help="The channel that SAM is broadcasting the detections on", default=None, required=False)
    parser.add_argument("--redis_connect", action="store_true", help="whether to immediately connect to the Redis host", required=False, default=None)
    parser.add_argument("--marker_size", metavar="INT", help="The size in pixels for the SAM points", default=None, type=int, required=False)
    parser.add_argument("--marker_color", metavar="HEXCOLOR", help="the color to use for the SAM points (hex color)", default=None, required=False)
    parser.add_argument("--min_obj_size", metavar="INT", help="The minimum size that SAM contours need to have (<= 0 for no minimum)", default=None, type=int, required=False)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size", default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual", default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size", default=None, required=False)
    parser.add_argument("--preprocessing", metavar="PIPELINE", help="the preprocessors to apply to the scan", default=None, required=False)
    parser.add_argument("--log_timestamp_format", metavar="FORMAT", help="the format string for the logging timestamp, see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes", default=LOG_TIMESTAMP_FORMAT, required=False)
    parser.add_argument("--zoom", metavar="PERCENT", help="the initial zoom to use (%%) or -1 for automatic fit", default=-1, type=int, required=False)
    parser.add_argument("--normalization", metavar="PLUGIN", help="the normalization plugin and its options to use", default=SimpleNormalization().name(), type=str, required=False)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)
    set_logging_level(logger, parsed.logging_level)
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
