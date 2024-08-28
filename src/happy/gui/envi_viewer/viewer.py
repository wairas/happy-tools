#!/usr/bin/python3
import argparse
import copy
import io
import logging
import matplotlib.pyplot as plt
import os
import pathlib
import pygubu
import queue
import subprocess
import sys
import traceback
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser

from datetime import datetime
from PIL import ImageTk, Image
from threading import Thread
from tkinter import filedialog as fd
from tkinter import messagebox
from ttkSimpleDialog import ttkSimpleDialog
from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data.normalization import SimpleNormalization
from happy.data import LABEL_WHITEREF, LABEL_BLACKREF
from happy.data import DataManager, export_sub_images
from happy.data.annotations import Contour, BRUSH_SHAPES, tableau_colors, MASK_PREFIX
from happy.gui import ToolTip, URL_PROJECT, URL_TOOLS, URL_PLUGINS
from happy.gui.dialog import asklist
from happy.gui.envi_viewer import SamManager, SessionManager, PROPERTIES
from happy.gui.envi_viewer import ANNOTATION_MODES, ANNOTATION_MODE_POLYGONS, ANNOTATION_MODE_PIXELS, generate_color_key
from happy.gui.envi_viewer.annotations import AnnotationsDialog
from happy.gui.envi_viewer.image import ImageDialog
from happy.gui.envi_viewer.sub_images import show_sub_images_dialog, KEY_OUTPUT_DIR, KEY_LABEL_REGEXP, \
    KEY_OUTPUT_FORMAT, KEY_RAW_SPECTRA
from happy.gui import UndoManager, remove_modifiers, show_busy_cursor, show_normal_cursor
from opex import ObjectPredictions

PROG = "happy-envi-viewer"

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "viewer.ui"

DIMENSIONS = "H: %d, W: %d, C: %d"

logger = logging.getLogger(PROG)

LOG_TIMESTAMP_FORMAT = "[%H:%M:%S.%f]"

log_queue = queue.Queue()
""" queue for logging messages from the DataManager instance. """


def check_log_queue(app, q):
    """
    Checks whether there are any messages in the log_queue and logs any messages via the app.

    :param app: the viewer app to use for logging
    :param q: the queue to check
    :type q: queue.Queue
    """
    try:
        while app.running:
            result = q.get_nowait()
            app.log(result)
    except queue.Empty:
        pass
    if app.running:
        app.mainwindow.after(100, check_log_queue, app, q)


def perform_image_update(app, rgb):
    success = app.data.update_image(rgb[0], rgb[1], rgb[2])
    app.mainwindow.after(100, app.display_updated_image, success)


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
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_window_closing)

        # setting theme
        style = ttk.Style(self.mainwindow)
        style.theme_use('clam')

        # attach variables to app itself
        self.state_keep_aspectratio = None
        self.state_autodetect_channels = None
        self.state_check_scan_dimensions = None
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
        self.state_export_to_scan_dir = None
        self.state_export_overlay_annotations = None
        self.state_export_keep_aspectratio = None
        self.state_export_enforce_mask_prefix = None
        self.state_black_ref_locator = None
        self.state_black_ref_method = None
        self.state_white_ref_locator = None
        self.state_white_ref_method = None
        self.state_normalization = None
        self.state_edit_annotation_mode = None
        self.state_pixels_brush_shape = None
        self.state_pixels_brush_color = None
        self.state_view_show_polygons = None
        self.state_view_show_pixels = None
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
        # file
        self.mainwindow.bind("<Control-o>", self.on_file_open_scan_click)
        self.mainwindow.bind("<Alt-x>", self.on_file_close_click)
        # edit
        self.mainwindow.bind("<Control-z>", self.on_edit_undo_click)
        self.mainwindow.bind("<Control-y>", self.on_edit_redo_click)
        self.mainwindow.bind("<Alt-n>", self.on_edit_markers_clear_click)
        # polygons
        self.mainwindow.bind("<Control-n>", self.on_polygons_clear_click)
        self.mainwindow.bind("<Control-e>", self.on_polygons_modify_click)
        self.mainwindow.bind("<Control-s>", self.on_polygons_run_sam_click)
        self.mainwindow.bind("<Control-p>", self.on_polygons_add_polygon_click)
        # pixels
        self.mainwindow.bind("<Control-N>", self.on_pixels_clear_click)
        self.mainwindow.bind("<Control-B>", self.on_pixels_brush_size_click)
        self.mainwindow.bind("<Control-A>", self.on_pixels_change_alpha_click)
        self.mainwindow.bind("<Control-L>", self.on_pixels_select_label_click)
        self.mainwindow.bind("<Control-K>", self.on_pixels_label_key)
        # view
        self.mainwindow.bind("<Control-w>", self.on_view_view_spectra_click)
        self.mainwindow.bind("<Control-W>", self.on_view_view_spectra_processed_click)
        # shift key for changing mouse cursor
        self.mainwindow.bind("<KeyPress-Shift_L>", self.on_image_shift_pressed)
        self.mainwindow.bind("<KeyPress-Shift_R>", self.on_image_shift_pressed)
        self.mainwindow.bind("<KeyRelease-Shift_L>", self.on_image_shift_released)
        self.mainwindow.bind("<KeyRelease-Shift_R>", self.on_image_shift_released)

        # mouse events
        # https://tkinterexamples.com/events/mouse/
        self.image_canvas.bind("<Button-1>", self.on_image_click)
        self.image_canvas.bind("<B1-Motion>", self.on_image_drag)
        self.label_r_value.bind("<Button-1>", self.on_label_r_click)
        self.label_g_value.bind("<Button-1>", self.on_label_g_click)
        self.label_b_value.bind("<Button-1>", self.on_label_b_click)

        # init some vars
        self.photo_scan = None
        self.session = SessionManager(log_method=self.log)
        self.data = DataManager(log_method=self.queue_log)
        self.last_dims = None
        self.last_wavelengths = None
        self.sam = SamManager()
        self.spectra_plot_raw = None
        self.spectra_plot_processed = None
        self.ignore_updates = False
        self.undo_manager = UndoManager(log_method=self.log)
        self.annotation_mode = ANNOTATION_MODE_POLYGONS
        self.pixel_points = []
        self.drag_update_interval = 0.1
        self.drag_start = None
        self.shift_pressed = False
        self.running = True
        self.busy = False

        # tooltips
        self.label_calc_norm_data_tooltip = ToolTip(self.label_calc_norm_data,
                                                    text=self.data.calc_norm_data_indicator_help(), wraplength=250)

    def run(self):
        check_log_queue(self, log_queue)
        self.mainwindow.mainloop()

    def on_window_closing(self, event=None):
        self.running = False

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

    def queue_log(self, msg):
        """
        Queues the log messages.

        :param msg: the message to queue/log
        :type msg: str
        """
        log_queue.put(msg)

    def start_busy(self):
        """
        Displays the hourglass cursor.
        """
        show_busy_cursor(self.mainwindow)
        self.busy = True

    def stop_busy(self):
        """
        Displays the normal cursor.
        """
        show_normal_cursor(self.mainwindow)
        self.busy = False

    def available(self, annotation_mode, show_error=True, action=None):
        """
        Checks whether the annotation_mode is the same as the currently selected one.

        :param annotation_mode: the mode to check
        :type annotation_mode: str
        :param show_error: whether to display an error message
        :type show_error: bool
        :param action: the action that is not available
        :type action: str
        :return: True if current and supplied mode are the same
        :rtype: bool
        """
        result = (annotation_mode == self.annotation_mode)
        if show_error and not result:
            msg = "Not available in annotation mode '%s'!" % self.annotation_mode
            if action is not None:
                msg += "\n" + action
            messagebox.showerror("Error", msg)
        return result

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

    def open_annotation_file(self, title, file_type, initial_dir):
        """
        Allows the user to select an OPEX JSON or ENVI mask annotation file.

        :param title: the title for the open dialog
        :type title: str
        :param file_type: the type of file (envi|opex)
        :type file_type: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        if file_type == "envi":
            filetypes = (
                ('ENVI files', '*.hdr'),
            )
        elif file_type == "opex":
            filetypes = (
                ('OPEX JSON files', '*.json'),
            )
        else:
            raise Exception("Unsupported annotation file type: %s" % file_type)

        filename = fd.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=filetypes)
        if filename == "":
            filename = None
        if isinstance(filename, tuple):
            filename = None

        return filename

    def save_file(self, title, file_type, initial_dir, scan=None):
        """
        Allows the user to select a PNG file for saving an image.

        :param title: the title to use for the save dialog
        :type title: str
        :param file_type: the type of file to save (png|envi|opex)
        :type file_type: str
        :param initial_dir: the initial directory in use
        :type initial_dir: str
        :param scan: the scan image to use for a suggestion
        :type scan: str
        :return: the chosen filename, None if cancelled
        :rtype: str
        """
        if file_type == "png":
            ext = ".png"
            filetypes = (
                ('PNG files', '*' + ext),
                ('All files', '*.*')
            )
        elif file_type == "envi":
            ext = ".hdr"
            filetypes = (
                ('ENVI files', '*' + ext),
                ('All files', '*.*')
            )
        elif file_type == "opex":
            ext = ".json"
            filetypes = (
                ('OPEX JSON files', '*' + ext),
                ('All files', '*.*')
            )
        else:
            raise Exception("Unsupported file type: %s" % file_type)

        initial_file = None
        if scan is not None:
            initial_file = os.path.splitext(os.path.basename(scan))[0] + ext

        filename = fd.asksaveasfilename(
            title=title,
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=filetypes)
        if isinstance(filename, tuple):
            filename = None
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
        self.data.markers.clear()
        self.data.contours.clear()
        self.data.pixels.clear()

        if self.data.has_scan():
            self.last_dims = self.data.scan_data.shape
            self.last_wavelengths = copy.copy(self.data.get_wavelengths())

        self.log("Loading scan: %s" % filename)
        self.session.last_scan_file = filename
        self.start_busy()
        warning = self.data.load_scan(filename)
        self.stop_busy()
        if warning is not None:
            messagebox.showerror("Warning", warning)

        # different dimensions?
        if self.session.check_scan_dimensions:
            if (self.last_dims is not None) and (self.data.has_scan()):
                if self.last_dims != self.data.scan_data.shape:
                    warning = "Different data dimensions detected: last=%s, new=%s" % (
                    str(self.last_dims), str(self.data.scan_data.shape))
                    messagebox.showwarning("Different dimensions", warning)
                elif self.last_wavelengths != self.data.get_wavelengths():
                    self.log("Last wavelengths: %s" % str(self.last_wavelengths))
                    self.log("Current wavelengths: %s" % str(self.data.get_wavelengths()))
                    messagebox.showwarning("Different wavelengths",
                                           "Different wavelengths detected (see console for last/current)!")

        # configure scales
        self.set_data_dimensions(self.data.scan_data.shape, do_update=False)

        # configure pixel annotations
        self.data.pixels.reshape(self.data.scan_data.shape[1], self.data.scan_data.shape[0])

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
        error = self.data.load_blackref(filename)
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
        error = self.data.load_whiteref(filename)
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
            self.state_scale_r.set(num_bands - 1)
        if g >= num_bands:
            self.state_scale_g.set(num_bands - 1)
        if b >= num_bands:
            self.state_scale_b.set(num_bands - 1)
        self.label_dims.configure(text=DIMENSIONS % dimensions)

        # update text
        self.on_scale_r_changed(None)
        self.on_scale_g_changed(None)
        self.on_scale_b_changed(None)

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
            self.image_canvas.delete("all")
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
            image_markers = self.data.markers.to_overlay(width, height, int(self.entry_marker_size.get()),
                                                         self.entry_marker_color.get())
            if image_markers is not None:
                image.paste(image_markers, (0, 0), image_markers)
            if self.session.show_polygon_annotations:
                image_contours = self.data.contours.to_overlay(width, height, self.entry_annotation_color.get())
                if image_contours is not None:
                    image.paste(image_contours, (0, 0), image_contours)
            if self.session.show_pixel_annotations:
                image_pixels = self.data.pixels.to_overlay(width, height)
                if image_pixels is not None:
                    image.paste(image_pixels, (0, 0), image_pixels)
            self.photo_scan = ImageTk.PhotoImage(image=image)
            self.image_canvas.create_image(0, 0, image=self.photo_scan, anchor=tk.NW)
            self.image_canvas.config(width=width, height=height)
            self.image_canvas.configure(scrollregion=(0, 0, width - 2, height - 2))
            # calc/set zoom for cursor in pixel manager
            self.data.pixels.zoom_x = width / self.data.scan_data.shape[1]
            self.data.pixels.zoom_y = height / self.data.scan_data.shape[0]

    def update_title(self):
        """
        Updates the title of the main window.
        """
        title = "ENVI Viewer"
        if self.data.scan_file is not None:
            title += ": " + os.path.basename(self.data.scan_file)
        self.mainwindow.title(title)

    def update_image(self, show_busy=True):
        """
        Updates the image.
        """
        if self.ignore_updates:
            return
        if show_busy:
            self.start_busy()
        rgb = (int(self.red_scale.get()), int(self.green_scale.get()), int(self.blue_scale.get()))
        thread = Thread(target=perform_image_update, args=(self, rgb))
        thread.start()

    def display_updated_image(self, success):
        if self.data.norm_data is not None:
            self.set_data_dimensions(self.data.norm_data.shape, do_update=False)
        elif self.data.scan_data is not None:
            self.set_data_dimensions(self.data.scan_data.shape, do_update=False)
        self.update_info()
        # make visible in UI
        if len(success) > 0:
            self.label_calc_norm_data["text"] = self.data.calc_norm_data_indicator(success)
            self.log("calc_norm_data steps: " + str(success))
        self.resize_image_canvas()
        self.log("")
        self.stop_busy()

    def update_info(self):
        """
        Updates the information.
        """
        self.text_info.delete(1.0, tk.END)
        self.text_info.insert(tk.END, self.data.info())

    def update(self):
        """
        Updates image and info.
        """
        if self.ignore_updates:
            return
        self.update_title()
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
        self.log("Setting SAM options: marker_size=%d marker_color=%s min_obj_size=%d" % (
        marker_size, marker_color, min_obj_size))
        self.state_marker_size.set(marker_size)
        self.state_marker_color.set(marker_color)
        self.state_min_obj_size.set(min_obj_size)

    def add_marker(self, event):
        """
        Adds a marker using the event coordinates.

        :param event: the event that triggered the adding
        """
        if not self.data.has_scan():
            return

        self.undo_manager.add_undo("Adding marker", self.get_undo_state())
        x = self.image_canvas.canvasx(event.x) / self.photo_scan.width()
        y = self.image_canvas.canvasy(event.y) / self.photo_scan.height()
        point = (x, y)
        self.data.markers.add(point)
        self.log("Marker point added: %s" % str(point))
        self.update_image()

    def get_predefined_labels(self, insert_empty_label=True):
        """
        Returns the list of predefined labels (if any).

        :param insert_empty_label: whether to insert the empty label as first item
        :type insert_empty_label: bool
        :return: the list of labels or None if not defined
        :rtype: list
        """
        if len(self.state_predefined_labels.get()) > 0:
            result = [x.strip() for x in self.state_predefined_labels.get().split(",")]
            if insert_empty_label and ("" not in result):
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
        contours = self.data.contours.contains(x, y)
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
        self.data.markers.clear()
        self.log("Marker points cleared")

    def remove_annotations(self, event):
        """
        Removes annotations that the click position covers.
        """
        x = self.image_canvas.canvasx(event.x) / self.photo_scan.width()
        y = self.image_canvas.canvasy(event.y) / self.photo_scan.height()
        contours = self.data.contours.contains(x, y)
        if len(contours) > 0:
            answer = messagebox.askquestion("Remove annotations", "Remove %d annotations?" % len(contours))
            if answer == messagebox.YES:
                self.data.contours.remove(contours)
            self.update_image()

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
        self.session.export_to_scan_dir = (self.state_export_to_scan_dir.get() == 1)
        self.session.export_overlay_annotations = self.state_export_overlay_annotations.get() == 1
        self.session.export_keep_aspectratio = self.state_export_keep_aspectratio.get() == 1
        self.session.export_enforce_mask_prefix = self.state_export_enforce_mask_prefix.get() == 1
        self.session.normalization = self.state_normalization.get()
        self.session.annotation_mode = self.annotation_mode
        self.session.brush_shape = self.data.pixels.brush_shape
        self.session.brush_size = self.data.pixels.brush_size
        self.session.invert_cursor = self.state_pixels_brush_color.get() == 1
        self.data.pixels.invert_cursor = self.state_pixels_brush_color.get() == 1
        self.session.alpha = self.data.pixels.alpha
        # zoom
        self.session.show_polygon_annotations = self.state_view_show_polygons.get() == 1
        self.session.show_pixel_annotations = self.state_view_show_pixels.get() == 1

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
        self.state_export_to_scan_dir.set(1 if self.session.export_to_scan_dir else 0)
        self.state_export_overlay_annotations.set(1 if self.session.export_overlay_annotations else 0)
        self.state_export_keep_aspectratio.set(1 if self.session.export_keep_aspectratio else 0)
        self.state_export_enforce_mask_prefix.set(1 if self.session.export_enforce_mask_prefix else 0)
        self.state_normalization.set(self.session.normalization)
        self.data.pixels.brush_shape = self.session.brush_shape
        self.data.pixels.invert_cursor = self.session.invert_cursor
        self.state_pixels_brush_color.set(1 if self.session.invert_cursor else 0)
        self.data.pixels.brush_size = self.session.brush_size
        self.data.pixels.alpha = self.session.alpha
        # zoom
        self.state_view_show_polygons.set(1 if self.session.show_polygon_annotations else 0)
        self.state_view_show_pixels.set(1 if self.session.show_pixel_annotations else 0)

        # activate
        self.ignore_updates = True
        self.state_edit_annotation_mode.set(ANNOTATION_MODES.index(self.session.annotation_mode))
        self.switch_annotation_mode(self.session.annotation_mode)
        self.state_pixels_brush_shape.set(BRUSH_SHAPES.index(self.data.pixels.brush_shape))
        self.ignore_updates = False
        self.apply_black_ref(do_update=False)
        self.apply_white_ref(do_update=False)
        self.apply_preprocessing(do_update=False)

    def get_undo_state(self):
        """
        Returns the state of the annotations as dictionary.

        :return: the dictionary
        :rtype: dict
        """
        return self.data.backup_state()

    def restore_undo_state(self, d):
        """
        Restores the state of the annotations from the dictionary.

        :param d: the state dictionary
        :type d: dict
        """
        self.data.restore_state(d)

    def apply_black_ref(self, do_update=False):
        # locator
        cmdline = self.state_black_ref_locator.get()
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_blackref_locator(cmdline)
                self.session.black_ref_locator = cmdline
                self.log("Setting black ref locator: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse reference locator: %s" % cmdline)
                return False
        else:
            self.data.set_blackref_locator(None)
            self.session.black_ref_locator = ""
            self.log("Removing black ref locator")

        # method
        cmdline = self.state_black_ref_method.get()
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_blackref_method(cmdline)
                self.session.black_ref_method = cmdline
                self.log("Setting black ref method: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse black reference method: %s" % cmdline)
                return False
        else:
            self.data.set_blackref_method(None)
            self.session.black_ref_method = ""
            self.log("Removing black ref method")

        if do_update:
            self.update_image()

        return True

    def apply_white_ref(self, do_update=False):
        # locator
        cmdline = self.state_white_ref_locator.get()
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_whiteref_locator(cmdline)
                self.session.white_ref_locator = cmdline
                self.log("Setting white ref locator: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse reference locator: %s" % cmdline)
                return False
        else:
            self.data.set_whiteref_locator(None)
            self.session.white_ref_locator = ""
            self.log("Removing white ref locator")

        # method
        cmdline = self.state_white_ref_method.get()
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_whiteref_method(cmdline)
                self.session.white_ref_method = cmdline
                self.log("Setting white ref method: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse white reference method: %s" % cmdline)
                return False
        else:
            self.data.set_whiteref_method(None)
            self.session.white_ref_method = ""
            self.log("Removing white ref method")

        if do_update:
            self.update_image()
        return True

    def apply_preprocessing(self, do_update=False):
        cmdline = self.text_preprocessing.get("1.0", "end-1c")
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_preprocessors(cmdline)
                self.log("Setting preprocessing: %s" % cmdline)
            except:
                messagebox.showerror("Error", "Failed to parse preprocessing: %s" % cmdline)
                return False
        else:
            self.data.set_preprocessors(None)
            self.log("Removing preprocessing")
        if do_update:
            self.update_image()
        return True

    def apply_normalization(self, do_update=False):
        cmdline = self.entry_normalization.get()
        if len(cmdline.strip()) > 0:
            try:
                self.data.set_normalization(cmdline)
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
        wl = None
        if self.data.norm_data is not None:
            wl = self.data.get_wavelengths_norm_list()
        elif self.data.has_scan():
            wl = self.data.get_wavelengths_list()
        if wl is None:
            return str(index)
        try:
            return str(index) + ": " + str(wl[index])
        except:
            return str(index)

    def on_file_clear_all_click(self, event=None):
        """
        Removes all loaded scans/annotations.
        """
        self.log("Clearing all")
        self.undo_manager.clear()
        self.data.clear_all()
        self.update()

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

    def on_file_import_blackref_annotations(self, event=None):
        """
        Allows the user to select annotations for the black reference ENVI file.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if not self.data.has_blackref():
            messagebox.showerror("Error", "Please load a black reference file first!")
            return

        filename = self.open_annotation_file('Import ref polygon annotations', "opex", self.session.last_blackref_dir)
        if filename is None:
            return
        self.log("Importing black ref OPEX JSON annotations: %s" % filename)
        preds = ObjectPredictions.load_json_from_file(filename)
        if len(self.state_predefined_labels.get()) > 0:
            blackref_obj = None
            for obj in preds.objects:
                if obj.label == LABEL_BLACKREF:
                    blackref_obj = obj
                    break
            if blackref_obj is None:
                messagebox.showwarning(
                    "Error",
                    "Failed to locate label '%s' in black reference annotations:\n%s" % (LABEL_BLACKREF, filename))
                return
            ann = (blackref_obj.bbox.top, blackref_obj.bbox.left, blackref_obj.bbox.bottom, blackref_obj.bbox.right)
            self.data.set_blackref_annotation(ann, False)
            self.update()

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

    def on_file_import_whiteref_annotations(self, event=None):
        """
        Allows the user to select annotations for the white reference ENVI file.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if not self.data.has_whiteref():
            messagebox.showerror("Error", "Please load a white reference file first!")
            return

        filename = self.open_annotation_file('Import white ref polygon annotations', "opex",
                                             self.session.last_whiteref_dir)
        if filename is None:
            return
        self.log("Importing white ref OPEX JSON annotations: %s" % filename)
        preds = ObjectPredictions.load_json_from_file(filename)
        if len(self.state_predefined_labels.get()) > 0:
            whiteref_obj = None
            for obj in preds.objects:
                if obj.label == LABEL_WHITEREF:
                    whiteref_obj = obj
                    break
            if whiteref_obj is None:
                messagebox.showwarning(
                    "Error",
                    "Failed to locate label '%s' in white reference annotations:\n%s" % (LABEL_WHITEREF, filename))
                return
            ann = (whiteref_obj.bbox.top, whiteref_obj.bbox.left, whiteref_obj.bbox.bottom, whiteref_obj.bbox.right)
            self.data.set_whiteref_annotation(ann, False)
            self.update()

    def on_file_import_pixel_annotations_click(self, event=None):
        """
        Allows the user to import existing annotations.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_annotation_file('Open pixel annotations', "envi", self.session.last_scan_dir)
        if filename is None:
            return

        self.log("Loading ENVI mask annotations: %s" % filename)
        self.undo_manager.add_undo("Importing pixel annotations", self.get_undo_state())
        self.data.pixels.load_envi(filename)
        self.data.pixels.clear_label_map()
        label_map = os.path.splitext(filename)[0] + ".json"
        if os.path.exists(label_map):
            msg = self.data.pixels.load_label_map(label_map)
            if msg is None:
                if len(self.state_predefined_labels.get()) > 0:
                    pre_labels = [x.strip() for x in self.state_predefined_labels.get().split(",")]
                    cur_labels = [x for x in self.data.pixels.label_map.values()]
                    missing_labels = set()
                    for cur_label in cur_labels:
                        if cur_label not in pre_labels:
                            missing_labels.add(cur_label)
                    if len(missing_labels) > 0:
                        missing_labels = sorted(list(missing_labels))
                        messagebox.showwarning(
                            "Warning",
                            "The following labels from the imported annotations are not listed under the predefined labels:\n" + ",".join(
                                missing_labels))
                    if len(self.data.pixels.unique_values()) != len(cur_labels):
                        messagebox.showwarning(
                            "Warning",
                            "Number of predefined labels and annotation labels differ:\npredefined: %s\nannotations:%s" % (
                            self.state_predefined_labels.get(), ",".join(cur_labels)))
            else:
                messagebox.showwarning("Error", msg)
        self.update_image()

    def on_file_import_polygon_annotations_click(self, event=None):
        """
        Allows the user to import existing annotations.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

        filename = self.open_annotation_file('Open polygon annotations', "opex", self.session.last_scan_dir)
        if filename is None:
            return
        self.log("Loading OPEX JSON annotations: %s" % filename)
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
                    "The following labels from the imported annotations are not listed under the predefined labels:\n" + ",".join(
                        missing_labels))
        self.undo_manager.add_undo("Importing polygon annotations", self.get_undo_state())
        self.data.contours.from_opex(preds, self.data.scan_data.shape[1], self.data.scan_data.shape[0])
        self.data.reset_norm_data()
        self.update_image()

    def on_file_export_image_click(self, event=None):
        """
        Allows the user to select a PNG file for saving the false color RGB to.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return

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
            # markers
            image_markers = self.data.markers.to_overlay(dims[0], dims[1], int(self.entry_marker_size.get()),
                                                         self.entry_marker_color.get())
            if image_markers is not None:
                image.paste(image_markers, (0, 0), image_markers)
            # polygons
            image_contours = self.data.contours.to_overlay(dims[0], dims[1], self.entry_annotation_color.get())
            if image_contours is not None:
                image.paste(image_contours, (0, 0), image_contours)
            # pixels
            image_pixels = self.data.pixels.to_overlay(dims[0], dims[1])
            if image_pixels is not None:
                image.paste(image_pixels, (0, 0), image_pixels)
            else:
                self.log("WARNING: Can't overlay annotations in mode '%s'!" % self.annotation_mode)

        if self.session.export_to_scan_dir:
            initial_dir = os.path.dirname(self.data.scan_file)
        else:
            initial_dir = self.session.last_image_dir
        filename = self.save_file('Save image', "png", initial_dir, scan=self.session.last_scan_file)
        if filename is not None:
            self.session.last_image_dir = os.path.dirname(filename)
            image.save(filename)
            self.log("Image saved to: %s" % filename)

    def on_file_export_polygon_annotations_click(self, event=None):
        """
        Allows the user to export polygon annotations.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if not self.data.contours.has_annotations():
            messagebox.showerror("Error", "Please create polygon annotations first!")
            return

        if self.session.export_keep_aspectratio:
            dims = self.data.dims()
        else:
            dims = self.get_image_canvas_dims()
        if dims is None:
            return
        dims = self.fit_image_into_dims(dims[0], dims[1], self.session.export_keep_aspectratio)

        if self.session.export_to_scan_dir:
            initial_dir = os.path.dirname(self.data.scan_file)
        else:
            initial_dir = self.session.last_image_dir
        filename = self.save_file('Save polygon annotations', "opex", initial_dir, scan=self.session.last_scan_file)
        if filename is None:
            return

        annotations = self.data.contours.to_opex(dims[0], dims[1])
        if annotations is not None:
            annotations.save_json_to_file(filename)
            self.log("OPEX JSON annotations saved to: %s" % filename)

    def on_file_export_pixel_annotations_click(self, event=None):
        """
        Allows the user to export pixel annotations.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if not self.data.pixels.has_annotations():
            messagebox.showerror("Error", "Please create pixel annotations first!")
            return

        if self.session.export_to_scan_dir:
            initial_dir = os.path.dirname(self.data.scan_file)
        else:
            initial_dir = self.session.last_image_dir
        filename = self.save_file('Save pixel annotations', "envi", initial_dir, scan=self.session.last_scan_file)
        if filename is None:
            return

        if self.session.export_enforce_mask_prefix:
            if not os.path.basename(filename).startswith(MASK_PREFIX):
                messagebox.showerror("Error", "Please pixel annotations filename must start with %s!" % MASK_PREFIX)
                return

        if self.data.pixels.save_envi(filename):
            self.log("ENVI Mask annotations saved to: %s" % filename)
        else:
            self.log("ERROR: Failed to save ENVI Mask annotations to: %s" % filename)
        filename = os.path.join(os.path.dirname(filename), os.path.splitext(os.path.basename(filename))[0] + ".json")
        if self.data.pixels.save_label_map(filename):
            self.log("ENVI Mask label map saved to: %s" % filename)
        else:
            self.log("ERROR: Failed to save ENVI Mask label map to: %s" % filename)

    def on_file_export_sub_images_click(self, event=None):
        """
        Allows the user to export polygon annotations as separate images.
        """
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if not self.data.contours.has_annotations():
            messagebox.showerror("Error", "Please create polygon annotations first!")
            return

        params = {
            KEY_OUTPUT_DIR: self.session.export_sub_images_path,
            KEY_LABEL_REGEXP: self.session.export_sub_images_label_regexp,
            KEY_OUTPUT_FORMAT: self.session.export_sub_images_output_format,
            KEY_RAW_SPECTRA: self.session.export_sub_images_raw,
        }
        params = show_sub_images_dialog(self.mainwindow, params)
        if params is None:
            return
        self.session.export_sub_images_path = params[KEY_OUTPUT_DIR]
        self.session.export_sub_images_label_regexp = params[KEY_LABEL_REGEXP]
        self.session.export_sub_images_output_format = params[KEY_OUTPUT_FORMAT]
        self.session.export_sub_images_raw = params[KEY_RAW_SPECTRA]

        # export sub-images
        rgb = (int(self.red_scale.get()), int(self.green_scale.get()), int(self.blue_scale.get()))
        msg = export_sub_images(self.data, params[KEY_OUTPUT_DIR], params[KEY_LABEL_REGEXP], params[KEY_RAW_SPECTRA],
                                output_format=params[KEY_OUTPUT_FORMAT], rgb=rgb)
        if msg is not None:
            messagebox.showerror("Error", "Failed to export sub-images to %s:\n%s" % (str(params[KEY_OUTPUT_DIR]), msg))
        else:
            self.log("Sub-images exported.")

    def on_file_export_to_scan_dir_click(self, event=None):
        self.session.export_to_scan_dir = (self.state_export_to_scan_dir.get() == 1)

    def on_file_export_overlay_annotations(self, event=None):
        self.session.export_overlay_annotations = self.state_export_overlay_annotations.get() == 1

    def on_file_export_keep_aspectratio(self, event=None):
        self.session.export_keep_aspectratio = self.state_export_keep_aspectratio.get() == 1

    def on_file_export_enforce_mask_prefix(self, event=None):
        self.session.export_enforce_mask_prefix = self.state_export_enforce_mask_prefix.get() == 1

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
        self.running = False
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
        self.update_image(show_busy=False)

    def on_scale_g_changed(self, event):
        self.green_scale_value.configure(text=self.scale_to_text(self.state_scale_g.get()))
        self.session.scale_g = self.state_scale_g.get()
        self.update_image(show_busy=False)

    def on_scale_b_changed(self, event):
        self.blue_scale_value.configure(text=self.scale_to_text(self.state_scale_b.get()))
        self.session.scale_b = self.state_scale_b.get()
        self.update_image(show_busy=False)

    def on_window_resize(self, event):
        self.resize_image_canvas()

    def on_image_click(self, event=None):
        state = remove_modifiers(event.state)
        if self.annotation_mode == ANNOTATION_MODE_POLYGONS:
            # no modifier -> add marker
            if state == 0x0000:
                self.add_marker(event)
            # CTRL -> clear markers
            elif state == 0x0004:
                self.clear_markers()
            # SHIFT -> set label
            elif state == 0x0001:
                self.set_label(event)
            # CTRL+SHIFT -> remove annotation
            elif state == 0x0005:
                self.remove_annotations(event)
        elif self.annotation_mode == ANNOTATION_MODE_PIXELS:
            # no modifier -> add marker
            if state == 0x0000:
                self.add_marker(event)
            # SHIFT or CTRL+SHIFT
            elif (state == 0x0001) or (state == 0x0005):
                state += 0x0100
                x = int(self.image_canvas.canvasx(event.x) / self.photo_scan.width() * self.data.scan_data.shape[1])
                y = int(self.image_canvas.canvasy(event.y) / self.photo_scan.height() * self.data.scan_data.shape[0])
                self.pixel_points.append((x, y))
                self.draw_recorded_pixel_points(state, True)

    def draw_recorded_pixel_points(self, state, add_undo):
        """
        Updates the pixel annotations with the currently collected points.

        :param state: the state determining whether to add/remove points
        :type state: int
        :param add_undo: whether to add undo point
        :type add_undo: bool
        """
        if len(self.pixel_points) == 0:
            return
        # SHIFT -> add
        if state == 0x0101:
            if add_undo:
                self.undo_manager.add_undo("Adding pixels", self.get_undo_state())
            self.data.pixels.add(self.pixel_points)
        # CTRL+SHIFT -> remove
        elif state == 0x0105:
            if add_undo:
                self.undo_manager.add_undo("Removing pixels", self.get_undo_state())
            self.data.pixels.remove(self.pixel_points)
        self.pixel_points.clear()
        self.update_image()

    def on_image_drag(self, event=None):
        # started drag?
        if self.drag_start is None:
            self.drag_start = datetime.now()
        state = remove_modifiers(event.state)
        # with SHIFT or CTRL+SHIFT
        if (state == 0x0101) or (state == 0x0105):
            x = int(self.image_canvas.canvasx(event.x) / self.photo_scan.width() * self.data.scan_data.shape[1])
            y = int(self.image_canvas.canvasy(event.y) / self.photo_scan.height() * self.data.scan_data.shape[0])
            self.pixel_points.append((x, y))
        # update image?
        now = datetime.now()
        if (now - self.drag_start).total_seconds() >= self.drag_update_interval:
            self.draw_recorded_pixel_points(state, False)
            self.drag_start = now

    def on_image_drag_release(self, event=None):
        self.drag_start = None
        self.draw_recorded_pixel_points(remove_modifiers(event.state), True)

    def on_image_shift_pressed(self, event=None):
        self.shift_pressed = True
        self.update_pixels_annotation_cursor()

    def on_image_shift_released(self, event=None):
        self.shift_pressed = False
        self.update_pixels_annotation_cursor()

    def on_label_r_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Red channel",
            prompt="Please enter the channel to use as Red (0-%d):" % (self.data.get_num_bands_norm() - 1),
            initialvalue=self.state_scale_r.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.red_scale.set(new_channel)

    def on_label_g_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Green channel",
            prompt="Please enter the channel to use as Green (0-%d):" % (self.data.get_num_bands_norm() - 1),
            initialvalue=self.state_scale_g.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.green_scale.set(new_channel)

    def on_label_b_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Blue channel",
            prompt="Please enter the channel to use as Blue (0-%d):" % (self.data.get_num_bands_norm() - 1),
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

    def switch_annotation_mode(self, mode):
        if mode != self.annotation_mode:
            self.log("Switching annotation mode to: %s" % mode)
            self.annotation_mode = mode
            if self.annotation_mode == ANNOTATION_MODE_POLYGONS:
                self.image_canvas.unbind("<ButtonRelease-1>")
                self.image_canvas.unbind("<B1-Motion>")
                # ensure that polygons are visible
                self.state_view_show_polygons.set(1)
                self.on_view_show_polygons()
            elif self.annotation_mode == ANNOTATION_MODE_PIXELS:
                self.image_canvas.bind("<ButtonRelease-1>", self.on_image_drag_release)
                self.image_canvas.bind("<B1-Motion>", self.on_image_drag)
                # ensure that pixel annotations are visible
                self.state_view_show_pixels.set(1)
                self.on_view_show_pixels()
            else:
                raise Exception("Unhandled annotation mode: %s" % self.annotation_mode)
            self.update_image()

    def on_edit_annotation_mode_click(self, event=None):
        mode = ANNOTATION_MODES[self.state_edit_annotation_mode.get()]
        self.switch_annotation_mode(mode)

    def on_edit_metadata_clear_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        self.undo_manager.add_undo("Clearing meta-data", self.get_undo_state())
        self.data.metadata.clear()
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
        self.data.metadata.set(k, v)
        self.log("Meta-data set: %s=%s" % (k, v))
        self.log("Meta-data:\n%s" % self.data.metadata.to_json())

    def on_edit_metadata_remove_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        k = asklist(
            title="Meta-data",
            prompt="Please enter the name of the meta-data value to remove:",
            items=sorted(list(self.data.metadata.to_dict().keys())),
            parent=self.mainwindow)
        if (k is None) or (k == ""):
            return
        self.undo_manager.add_undo("Removing meta-data", self.get_undo_state())
        msg = self.data.metadata.remove(k)
        if msg is not None:
            messagebox.showwarning("Meta-data", msg)
        else:
            self.log("Meta-data:\n%s" % self.data.metadata.to_json())

    def on_edit_metadata_view_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showinfo("Info", "No data present!")
            return

        if len(self.data.metadata) == 0:
            messagebox.showinfo("Meta-data", "Currently no meta-data stored.")
            return
        s = ""
        d = self.data.metadata.to_dict()
        for k in d:
            s += "%s:\n  %s\n" % (k, d[k])
        self.log("Meta-data:\n%s" % self.data.metadata.to_json())
        messagebox.showinfo("Meta-data", "Current meta-data:\n\n%s" % s)

    def on_edit_markers_clear_click(self, event=None):
        self.undo_manager.add_undo("Clearing markers", self.get_undo_state())
        if self.data.markers.has_points():
            self.data.markers.clear()
            self.update_image()
            self.log("Marker points cleared")
        else:
            self.log("No marker points to clear")

    def on_polygons_clear_click(self, event=None):
        self.undo_manager.add_undo("Clearing polygons/markers", self.get_undo_state())
        if self.data.contours.has_annotations() or self.data.markers.has_points():
            self.data.contours.clear()
            self.data.markers.clear()
            self.update_image()
            self.log("Polygons/marker points cleared")
        else:
            self.log("No polygons/marker points to clear")

    def on_polygon_annotations_updated(self, changed, deleted):
        """
        Gets called when Polygons -> Modify dialog gets accepted.

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
            self.data.contours.remove(deleted)
        if len(changed) > 0:
            self.log("Updating labels for %d annotations" % len(changed))
            for c in changed:
                self.data.contours.update_label(c, c.label)
        self.update_image()

    def on_polygons_modify_click(self, event=None):
        if not self.data.has_scan():
            messagebox.showerror("Error", "Please load a scan file first!")
            return
        if len(self.data.contours.contours) == 0:
            messagebox.showerror("Error", "Please add annotations first!")
            return

        dialog = AnnotationsDialog(self.mainwindow, self.data.contours,
                                   self.data.scan_data.shape[1], self.data.scan_data.shape[0],
                                   predefined_labels=self.get_predefined_labels())
        dialog.show(self.on_polygon_annotations_updated)

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
        self.data.contours.add([Contour(points=x, meta=copy.copy(meta)) for x in contours])
        # update contours/image
        self.resize_image_canvas()

    def on_polygons_run_sam_click(self, event=None):
        if not self.sam.is_connected():
            messagebox.showerror("Error", "Not connected to Redis server, cannot communicate with SAM!")
            self.notebook.select(2)
            return
        if not self.data.markers.has_points():
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
        points = self.data.markers.to_absolute(self.image_canvas.winfo_width(), self.image_canvas.winfo_height())
        self.data.markers.clear()

        # predict contours
        self.sam.predict(content, points,
                         self.state_redis_in.get(), self.state_redis_out.get(),
                         self.state_min_obj_size.get(), self.log, self.on_sam_predictions)

    def on_pixels_clear_click(self, event=None):
        self.undo_manager.add_undo("Clearing pixels", self.get_undo_state())
        self.data.pixels.clear()
        self.update_image()

    def update_pixels_annotation_cursor(self):
        if not self.available(ANNOTATION_MODE_PIXELS, show_error=False):
            return
        if self.shift_pressed:
            if self.data.pixels.invert_cursor:
                self.image_canvas["cursor"] = ("@" + self.data.pixels.cursor_path, 'white')
            else:
                self.image_canvas["cursor"] = ("@" + self.data.pixels.cursor_path, 'black')
        else:
            self.image_canvas["cursor"] = ""

    def on_pixels_brush_shape_click(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Selecting brush shape"):
            return

        self.data.pixels.brush_shape = BRUSH_SHAPES[self.state_pixels_brush_shape.get()]
        self.update_pixels_annotation_cursor()

    def on_pixels_brush_color_click(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Selecting brush color"):
            return

        self.data.pixels.invert_cursor = self.state_pixels_brush_color.get() == 1
        self.update_pixels_annotation_cursor()

    def on_pixels_brush_size_click(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Setting brush size"):
            return

        size = ttkSimpleDialog.askinteger("Brush size", "Please enter brush size (>= 1):",
                                          initialvalue=self.data.pixels.brush_size)
        if size is None:
            return
        size = int(size)
        if size < 1:
            messagebox.showerror("Brush size", "Brush size must be at least 1 pixel, provided: %d" % size)
            return
        self.data.pixels.brush_size = size
        self.log("New brush size: %d" % size)
        self.update_pixels_annotation_cursor()

    def on_pixels_change_alpha_click(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Changing alpha"):
            return

        alpha = ttkSimpleDialog.askinteger(
            "Transparency", "Please enter new alpha (0-255, 0: transparent, 255: opaque):",
            initialvalue=self.data.pixels.alpha)
        if alpha is None:
            return
        alpha = int(alpha)
        if (alpha < 0) or (alpha > 255):
            messagebox.showerror("Transparency", "Alpha must be between 0 and 255, provided: %d" % alpha)
            return
        self.data.pixels.alpha = alpha
        self.log("New alpha: %d" % alpha)
        self.update_image()

    def on_pixels_select_label_click(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Selecting pixel label"):
            return

        index = self.data.pixels.label
        label = None
        labels = self.get_predefined_labels(insert_empty_label=False)
        if labels is not None:
            try:
                label = labels[index - 1]
            except:
                label = None
        if label is None:
            index = ttkSimpleDialog.askinteger(
                title="Enter label index", prompt="Please enter the index of the label (> 0):",
                initialvalue=index + 1)
            if index is not None:
                if (index > 0) and (index <= 255):
                    self.data.pixels.label = index
                    self.data.pixels.update_label_map(index, str(index))
                else:
                    messagebox.showerror("Incorrect label index",
                                         "The label index must be >0 and <=255, provided: %d" % index)
        else:
            label = asklist(
                title="Choose label", prompt="Please select the label to annotate:",
                items=labels, initialvalue=label)
            if label is not None:
                index = labels.index(label) + 1
                self.data.pixels.label = index
                self.data.pixels.update_label_map(index, label)

    def on_pixels_label_key(self, event=None):
        if not self.available(ANNOTATION_MODE_PIXELS, action="Displaying label key"):
            return

        labels = self.get_predefined_labels(insert_empty_label=False)
        if labels is None:
            labels = [str(x) for x in self.data.pixels.unique_values()]
        key_img = generate_color_key(tableau_colors(), labels)
        key_dlg = ImageDialog(self.mainwindow)
        key_dlg.show(key_img)

    def on_button_black_ref_apply(self, event=None):
        self.apply_black_ref(do_update=True)

    def on_button_white_ref_apply(self, event=None):
        self.apply_white_ref(do_update=True)

    def on_button_preprocessing_apply(self, event=None):
        self.apply_preprocessing(do_update=True)

    def on_button_normalization_apply(self, event=None):
        self.apply_normalization(do_update=True)

    def on_polygons_add_polygon_click(self, event=None):
        if not self.available(ANNOTATION_MODE_POLYGONS, action="Adding polygon"):
            return

        if not self.data.markers.has_polygon():
            messagebox.showerror("Error", "At least three marker points necessary to create a polygon!")
            return

        self.undo_manager.add_undo("Adding polygon", self.get_undo_state())
        self.data.contours.add([Contour(points=self.data.markers.points[:])])
        self.data.markers.clear()
        self.log("Polygon added")
        self.update_image()

    def on_view_show_polygons(self, event=None):
        self.session.show_polygon_annotations = (self.state_view_show_polygons.get() == 1)
        self.update_image()

    def on_view_show_pixels(self, event=None):
        self.session.show_pixel_annotations = (self.state_view_show_pixels.get() == 1)
        self.update_image()

    def on_view_view_spectra_click(self, event=None):
        if not self.data.markers.has_points():
            messagebox.showerror("Error", "No marker points present!")
            return

        points = self.data.markers.to_spectra(self.data.scan_data)
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

    def on_view_view_spectra_processed_click(self, event=None):
        if not self.data.markers.has_points():
            messagebox.showerror("Error", "No marker points present!")
            return

        points = self.data.markers.to_spectra(self.data.norm_data)
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

    def on_view_zoom_click(self, event=None):
        if (event is not None) and (event.startswith("command_view_zoom_")):
            try:
                zoom = int(event.replace("command_view_zoom_", ""))
                self.session.zoom = zoom
                self.update_image()
            except:
                self.log("Failed to extract zoom from: %s" % event)

    def on_view_zoom_fit(self, event=None):
        self.session.zoom = -1
        self.update_image()

    def on_view_zoom_custom(self, event=None):
        curr_zoom = self.session.zoom
        if curr_zoom <= 0:
            curr_zoom = -1
        new_zoom = ttkSimpleDialog.askinteger("Zoom", "Please enter new zoom (in %; -1 for best fit):",
                                              initialvalue=curr_zoom)
        if new_zoom is not None:
            if new_zoom <= 0:
                new_zoom = -1
            self.session.zoom = new_zoom
            self.update_image()

    def on_window_new_window_click(self, event=None):
        cmd = [sys.executable]
        cmd.extend(sys.argv[:])
        self.log("Launching: %s" % " ".join(cmd))
        subprocess.Popen(cmd)

    def on_window_half_height_click(self, event=None):
        w = self.mainwindow.winfo_width()
        h = self.mainwindow.winfo_screenheight() // 2
        self.mainwindow.geometry("%dx%d" % (w, h))

    def on_window_half_width_click(self, event=None):
        w = self.mainwindow.winfo_screenwidth() // 2
        h = self.mainwindow.winfo_height()
        self.mainwindow.geometry("%dx%d" % (w, h))

    def on_help_project_click(self, event=None):
        webbrowser.open(URL_PROJECT)

    def on_help_tools_click(self, event=None):
        webbrowser.open(URL_TOOLS)

    def on_help_plugins_click(self, event=None):
        webbrowser.open(URL_PLUGINS)

    def on_button_sam_connect_click(self, event=None):
        if self.sam.is_connected():
            self.log("Disconnecting SAM...")
            self.button_sam_connect.configure(text="Connect")
            self.sam.disconnect()
            self.label_redis_connection.configure(text="Disconnected")
        else:
            self.log("Connecting SAM...")
            if self.sam.connect(host=self.state_redis_host.get(), port=self.state_redis_port.get(),
                                pw=self.state_redis_pw.get()):
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
    parser.add_argument("-f", "--black_reference", type=str, help="Path to the black reference file (ENVI format)",
                        required=False)
    parser.add_argument("-w", "--white_reference", type=str, help="Path to the white reference file (ENVI format)",
                        required=False)
    parser.add_argument("-r", "--scale_r", metavar="INT", help="the wave length to use for the red channel",
                        default=None, type=int, required=False)
    parser.add_argument("-g", "--scale_g", metavar="INT", help="the wave length to use for the green channel",
                        default=None, type=int, required=False)
    parser.add_argument("-b", "--scale_b", metavar="INT", help="the wave length to use for the blue channel",
                        default=None, type=int, required=False)
    parser.add_argument("--autodetect_channels", action="store_true",
                        help="whether to determine the channels from the meta-data (overrides the manually specified channels)",
                        required=False, default=None)
    parser.add_argument("--no_autodetect_channels", action="store_true",
                        help="whether to turn off auto-detection of channels from meta-data", required=False,
                        default=None)
    parser.add_argument("--keep_aspectratio", action="store_true", help="whether to keep the aspect ratio",
                        required=False, default=None)
    parser.add_argument("--no_keep_aspectratio", action="store_true", help="whether to not keep the aspect ratio",
                        required=False, default=None)
    parser.add_argument("--check_scan_dimensions", action="store_true",
                        help="whether to compare the dimensions of subsequently loaded scans and output a warning if they differ",
                        required=False, default=None)
    parser.add_argument("--no_check_scan_dimensions", action="store_true",
                        help="whether to not compare the dimensions of subsequently loaded scans and output a warning if they differ",
                        required=False, default=None)
    parser.add_argument("--export_to_scan_dir", action="store_true",
                        help="whether to export images to the scan directory rather than the last one used",
                        required=False, default=None)
    parser.add_argument("--annotation_color", metavar="HEXCOLOR",
                        help="the color to use for the annotations like contours (hex color)", default=None,
                        required=False)
    parser.add_argument("--predefined_labels", metavar="LIST", help="the comma-separated list of labels to use",
                        default=None, required=False)
    parser.add_argument("--redis_host", metavar="HOST", type=str, help="The Redis host to connect to (IP or hostname)",
                        default=None, required=False)
    parser.add_argument("--redis_port", metavar="PORT", type=int, help="The port the Redis server is listening on",
                        default=None, required=False)
    parser.add_argument("--redis_pw", metavar="PASSWORD", type=str, help="The password to use with the Redis server",
                        default=None, required=False)
    parser.add_argument("--redis_in", metavar="CHANNEL", type=str, help="The channel that SAM is receiving images on",
                        default=None, required=False)
    parser.add_argument("--redis_out", metavar="CHANNEL", type=str,
                        help="The channel that SAM is broadcasting the detections on", default=None, required=False)
    parser.add_argument("--redis_connect", action="store_true", help="whether to immediately connect to the Redis host",
                        required=False, default=None)
    parser.add_argument("--no_redis_connect", action="store_true",
                        help="whether to not immediately connect to the Redis host", required=False, default=None)
    parser.add_argument("--marker_size", metavar="INT", help="The size in pixels for the SAM points", default=None,
                        type=int, required=False)
    parser.add_argument("--marker_color", metavar="HEXCOLOR", help="the color to use for the SAM points (hex color)",
                        default=None, required=False)
    parser.add_argument("--min_obj_size", metavar="INT",
                        help="The minimum size that SAM contours need to have (<= 0 for no minimum)", default=None,
                        type=int, required=False)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR",
                        help="the reference locator scheme to use for locating black references, eg rl-manual",
                        default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD",
                        help="the black reference method to use for applying black references, eg br-same-size",
                        default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR",
                        help="the reference locator scheme to use for locating whites references, eg rl-manual",
                        default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD",
                        help="the white reference method to use for applying white references, eg wr-same-size",
                        default=None, required=False)
    parser.add_argument("--preprocessing", metavar="PIPELINE", help="the preprocessors to apply to the scan",
                        default=None, required=False)
    parser.add_argument("--log_timestamp_format", metavar="FORMAT",
                        help="the format string for the logging timestamp, see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes",
                        default=LOG_TIMESTAMP_FORMAT, required=False)
    parser.add_argument("--zoom", metavar="PERCENT", help="the initial zoom to use (%%) or -1 for automatic fit",
                        default=-1, type=int, required=False)
    parser.add_argument("--normalization", metavar="PLUGIN", help="the normalization plugin and its options to use",
                        default=SimpleNormalization().name(), type=str, required=False)
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
    # check for --no_* flags to override any session values
    for p in PROPERTIES:
        if hasattr(parsed, "no_" + p):
            value = getattr(parsed, "no_" + p)
            if (value is not None) and value:
                setattr(app.session, p, False)
    app.session_to_state()

    if not app.session.autodetect_channels:
        app.set_wavelengths(app.session.scale_r, app.session.scale_g, app.session.scale_b)
    app.set_redis_connection(app.session.redis_host, app.session.redis_port, app.session.redis_pw, app.session.redis_in,
                             app.session.redis_out)
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
