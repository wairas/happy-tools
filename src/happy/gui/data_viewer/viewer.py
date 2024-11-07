#!/usr/bin/python3
import argparse
import logging
import os
import pathlib
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk
import traceback
import webbrowser
from threading import Thread
from tkinter import filedialog as fd
from tkinter import messagebox

import matplotlib.pyplot as plt
import numpy as np
import pygubu

from PIL import Image, ImageTk
from matplotlib.colors import Normalize
from ttkSimpleDialog import ttkSimpleDialog

from wai.logging import add_logging_level, set_logging_level
from happy.gui.data_viewer import SessionManager
from happy.readers import HappyReader
from happy.base.app import init_app
from happy.data.normalization import AbstractNormalization, SimpleNormalization, CHANNEL_RED, CHANNEL_GREEN, CHANNEL_BLUE
from happy.gui import URL_PROJECT, URL_TOOLS, URL_PLUGINS, show_busy_cursor, show_normal_cursor, ToolTip

PROG = "happy-data-viewer"

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "viewer.ui"

logger = logging.getLogger(PROG)


def perform_plot_update(app, canvas_width, canvas_height, show_busy):
    """
    Calculates the updated plot.

    :param app: the ViewerApp instance
    :param canvas_width: the width of the canvas
    :type canvas_width: int
    :param canvas_height: the height of the canvas
    :type canvas_height: int
    :param show_busy: whether to update the busy cursor
    :type show_busy: bool
    """
    if app.rgb_image is None:
        app.rgb_image = app.convert_to_rgb(app.stored_happy_data)

    rgb_image = app.rgb_image

    try:
        if (app.session.selected_metadata_key is not None) and (app.metadata_rgb_colors is not None):
            if app.combined_image is None:
                # Convert metadata RGB colors to a NumPy array
                overlay_image = app.metadata_rgb_colors
                # Apply transparency based on opacity slider value
                overlay_alpha = float(app.scale_opacity.get() / 100)  # Scale to 0-255
                # Convert hyperspectral RGB image to float
                rgb_image_float = np.array(rgb_image).astype(float) / 255.0
                # Combine hyperspectral image with the overlay image
                combined_image = (1.0 - overlay_alpha) * rgb_image_float + (overlay_image * overlay_alpha)
                # Clip values to ensure they are within [0, 1]
                combined_image = np.clip(combined_image, 0, 1)
                # Convert the combined image to uint8
                combined_image_uint8 = (combined_image * 255).astype(np.uint8)
                # Create an Image object from the combined image
                app.combined_image = Image.fromarray(combined_image_uint8)
            rgb_image = app.combined_image
    except:
        app.log("Failed to compute combined image:\n%s" % traceback.format_exc())

    # Calculate aspect ratio of the image
    width, height = rgb_image.size
    aspect_ratio = width / height

    # Calculate new dimensions while maintaining aspect ratio
    if app.session.zoom == -1:
        if canvas_width / aspect_ratio < canvas_height:
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = canvas_height
            new_width = int(new_height * aspect_ratio)
    else:
        new_width = int(width * app.session.zoom / 100)
        new_height = int(height * app.session.zoom / 100)

    # Resize the image using PIL
    rgb_image = rgb_image.resize((new_width, new_height), Image.LANCZOS)

    # Create a new PhotoImage object from the resized PIL image
    resized_image = ImageTk.PhotoImage(rgb_image)
    app.mainwindow.after(100, app.display_updated_plot, resized_image, new_width, new_height, show_busy)


class ViewerApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # main window
        self.mainwindow = builder.get_object("toplevel", master)
        builder.connect_callbacks(self)
        self.mainwindow.iconphoto(False, tk.PhotoImage(file=str(PROJECT_PATH) + '/../../logo.png'))
        self.mainwindow.bind("<Configure>", self.on_window_resize)

        # setting theme
        style = ttk.Style(self.mainwindow)
        style.theme_use('clam')

        # widgets
        self.label_dir = builder.get_object("label_dir", master)
        self.listbox_samples = builder.get_object("listbox_samples", master)
        self.listbox_regions = builder.get_object("listbox_regions", master)
        self.combobox_metadata = builder.get_object("combobox_type", master)
        self.scale_opacity = builder.get_object("scale_opacity", master)
        self.scale_r = builder.get_object("scale_r", master)
        self.scale_g = builder.get_object("scale_g", master)
        self.scale_b = builder.get_object("scale_b", master)
        self.label_r_value = builder.get_object("label_r_value", master)
        self.label_g_value = builder.get_object("label_g_value", master)
        self.label_b_value = builder.get_object("label_b_value", master)
        self.canvas = builder.get_object("canvas", master)

        # accelerators are just strings, we need to bind them to actual methods
        # https://tkinterexamples.com/events/keyboard/
        self.mainwindow.bind("<Control-o>", self.on_file_open_dir_click)
        self.mainwindow.bind("<Control-e>", self.on_file_export_image_click)
        self.mainwindow.bind("<Alt-x>", self.on_file_close_click)

        # listbox events
        self.listbox_samples.bind('<<ListboxSelect>>', self.on_listbox_samples_select)
        self.listbox_regions.bind('<<ListboxSelect>>', self.on_listbox_regions_select)

        # combobox events
        self.combobox_metadata.bind('<<ComboboxSelected>>', self.on_metadata_select)

        # mouse events
        # https://tkinterexamples.com/events/mouse/
        self.label_r_value.bind("<Button-1>", self.on_label_r_click)
        self.label_g_value.bind("<Button-1>", self.on_label_g_click)
        self.label_b_value.bind("<Button-1>", self.on_label_b_click)

        # states
        self.state_opacity = None
        self.state_scale_r = None
        self.state_scale_g = None
        self.state_scale_b = None
        self.var_listbox_samples = None
        self.var_listbox_regions = None
        builder.import_variables(self)

        # tooltips
        self.label_r_value_tooltip = ToolTip(self.label_r_value, "Click to select channel")
        self.label_g_value_tooltip = ToolTip(self.label_g_value, "Click to select channel")
        self.label_b_value_tooltip = ToolTip(self.label_b_value, "Click to select channel")

        # other variables
        self.session = SessionManager(log_method=self.log)
        self.reader = None
        self.updating = False
        self.stored_happy_data = None
        self.rgb_image = None
        self.combined_image = None
        self.metadata_values = None
        self.metadata_rgb_colors = None
        self.normalization = SimpleNormalization()
        self.normalization_cmdline = SimpleNormalization().name()

    def set_listbox_selectbackground(self, color):
        """
        Sets the background color to use for selected items in listboxes.

        :param color: the color
        :type color: str
        """
        self.listbox_samples.config(selectbackground=color)
        self.listbox_regions.config(selectbackground=color)

    def set_listbox_selectforeground(self, color):
        """
        Sets the foreground color to use for selected items in listboxes.

        :param color: the color
        :type color: str
        """
        self.listbox_samples.config(selectforeground=color)
        self.listbox_regions.config(selectforeground=color)

    def log(self, msg):
        """
        Simply outputs the supplied message.

        :param msg: the logging message to output
        :type msg: str
        """
        if msg != "":
            logger.info(msg)

    def clear_plot(self):
        """
        Clears any previous plot.
        """
        self.rgb_image = None
        self.combined_image = None
        self.canvas.delete("all")

    def start_busy(self):
        """
        Displays the hourglass cursor.
        """
        show_busy_cursor(self.mainwindow)

    def stop_busy(self):
        """
        Displays the normal cursor.
        """
        show_normal_cursor(self.mainwindow)

    def load(self, path, sample, region, metadata_key):
        """
        Loads the data using the base dir, sample and region.

        :param path: the path to load from, can be None
        :type path: str
        :param sample: the sample to load, can be None
        :type sample: str
        :param region: the region to load, can be None
        :type region: str
        :param metadata_key: the meta-data key to select, can be None
        :type metadata_key: str
        """
        self.clear_plot()

        # base dir
        if (path is None) or (len(path) == 0):
            return
        if not os.path.exists(path) or not os.path.isdir(path):
            return
        self.load_dir(path)

        # sample
        if (sample is None) or (len(sample) == 0):
            return
        self.updating = True
        found = False
        for i in range(self.listbox_samples.size()):
            s = self.listbox_samples.get(i)
            if s == sample:
                self.listbox_samples.selection_clear(0, "end")
                self.listbox_samples.selection_set(i)
                found = True
                break
        if not found:
            self.updating = False
            return
        self.load_sample(sample)
        self.updating = False

        # region
        if (region is None) or (len(region) == 0):
            return
        found = False
        for i in range(self.listbox_regions.size()):
            s = self.listbox_regions.get(i)
            if s == region:
                self.listbox_regions.selection_clear(0, "end")
                self.listbox_regions.selection_set(i)
                found = True
                break
        if not found:
            return
        self.load_region(region)

        # metadata key
        if (metadata_key is None) or (len(metadata_key) == 0):
            return
        self.select_metadata_key(metadata_key)

    def select_metadata_key(self, key):
        """
        Selects the specified meta-data key, if possible.

        :param key: the key to select
        :type key: str
        """
        if key is None:
            return
        keys = self.combobox_metadata['values']
        for i, k in enumerate(keys):
            if k == key:
                self.combobox_metadata.current(i)
                break

    def load_dir(self, path):
        """
        Opens the specified directory (threaded).

        :param path: the directory to load
        :type path: str
        """
        self.log("dir: %s" % path)
        self.label_dir.configure(text=path)
        self.session.current_dir = path
        self.reader = HappyReader(path)

        samples = []
        for f in os.listdir(path):
            if f.startswith("."):
                continue
            full = os.path.join(path, f)
            if os.path.isdir(full):
                samples.append(f)
        samples.sort()
        self.var_listbox_samples.set(samples)
        if not self.updating:
            self.clear_plot()
            if len(samples) > 0:
                self.listbox_regions.selection_clear(0, "end")
                self.listbox_samples.selection_set(0)
                self.on_listbox_samples_select()

    def load_sample(self, sample):
        """
        Loads the specified sample from the current directory (threaded).

        :param sample: the sample to load
        :type sample: str
        """
        self.log("sample: %s" % sample)
        self.session.current_sample = sample

        path = os.path.join(self.session.current_dir, sample)
        regions = []
        all_numeric = True
        for f in os.listdir(path):
            if f.startswith("."):
                continue
            full = os.path.join(path, f)
            if os.path.isdir(full):
                regions.append(f)
                if not f.isnumeric():
                    all_numeric = False
        # all numeric?
        if all_numeric:
            regions = [int(x) for x in regions]
            regions.sort()
            regions = [str(x) for x in regions]
        else:
            regions.sort()
        self.var_listbox_regions.set(regions)
        if not self.updating:
            self.clear_plot()
            if len(regions) > 0:
                self.listbox_regions.selection_clear(0, "end")
                self.listbox_regions.selection_set(0)
                self.on_listbox_regions_select()

    def load_region(self, region):
        """
        Loads the specified region from the current dir and sample (threaded).

        :param region: the region to load
        :type region: str
        """
        self.log("region: %s" % region)
        self.session.current_region = region
        self.clear_plot()
        self.load_happy_data()

    def load_happy_data(self):
        """
        Loads the current dir/sample/region and displays the image.
        """
        if (self.session.current_dir is None) or (self.session.current_sample is None) or (self.session.current_region is None):
            return
        full = os.path.join(self.session.current_dir, self.session.current_sample, self.session.current_region)
        if not os.path.exists(full) or not os.path.isdir(full):
            return

        self.start_busy()
        self.updating = True
        self.stored_happy_data = self.reader.load_data(self.session.current_sample + ":" + self.session.current_region)
        # Extract and store the metadata keys
        if self.stored_happy_data is not None:
            # collect metadata keys that have data stored
            metadata_keys = []
            for k in self.stored_happy_data[0].metadata_dict:
                if "data" in self.stored_happy_data[0].metadata_dict[k]:
                    metadata_keys.append(k)
            metadata_keys = sorted(metadata_keys)
            # update GUI
            self.update_metadata_combobox(metadata_keys)  # Call a new method to update the Combobox
            if self.session.selected_metadata_key is not None:
                if self.session.selected_metadata_key in self.stored_happy_data[0].metadata_dict:
                    metadata_values = self.stored_happy_data[0].metadata_dict[self.session.selected_metadata_key]["data"]
                    self.metadata_values = np.squeeze(metadata_values)
                    self.metadata_rgb_colors = self.map_metadata_to_rgb(self.metadata_values)

        self.log("Loaded HappyData: %s" % str(self.stored_happy_data))
        self.rgb_image = None
        self.combined_image = None
        num_channels = len(self.stored_happy_data[0].data[0, 0, :])

        # Update the range of existing sliders
        self.scale_r.config(from_=0, to=num_channels - 1)
        self.scale_g.config(from_=0, to=num_channels - 1)
        self.scale_b.config(from_=0, to=num_channels - 1)

        # Continue with loading and displaying HappyData...
        self.updating = False  # Allow updates after loading
        self.stop_busy()

        self.update_plot()

    def update_metadata_combobox(self, metadata_keys):
        """
        Update the values in the metadata combobox.

        :param metadata_keys: the keys to display
        :type metadata_keys: list
        """
        self.combobox_metadata['values'] = metadata_keys
        if len(metadata_keys) > 0:
            self.combobox_metadata.set(metadata_keys[0])  # Set the default selection

    def convert_to_rgb(self, happy_data):
        # Extract the hyperspectral data array
        hyperspectral_data = happy_data[0].data

        # Get the values of the R, G, and B channel sliders
        r = self.state_scale_r.get()
        g = self.state_scale_g.get()
        b = self.state_scale_b.get()

        # Use the slider values to select the corresponding channels from the data
        r_band = hyperspectral_data[:, :, r]
        g_band = hyperspectral_data[:, :, g]
        b_band = hyperspectral_data[:, :, b]

        r_normalized = r_band
        g_normalized = g_band
        b_normalized = b_band
        if self.normalization is not None:
            self.log("Applying normalization: %s" % self.normalization_cmdline)
            try:
                r_normalized = self.normalization.normalize(r_band, CHANNEL_RED)
                g_normalized = self.normalization.normalize(g_band, CHANNEL_GREEN)
                b_normalized = self.normalization.normalize(b_band, CHANNEL_BLUE)
            except:
                self.log("Failed to normalize image using r=%d, g=%d, b=%d:\n%s" % (r, g, b, traceback.format_exc()))

        # Create an RGB image using the normalized bands
        rgb_image = np.dstack((r_normalized, g_normalized, b_normalized))
        rgb_image = Image.fromarray((rgb_image * 255).astype(np.uint8))

        return rgb_image

    def update_plot(self, show_busy=True):
        """
        Updates the plot.

        :param show_busy: whether to show the busy cursor
        :type show_busy: bool
        """
        if self.updating:
            return
        if self.stored_happy_data is None:
            return

        # Calculate canvas dimensions (only once)
        canvas_width = self.canvas.winfo_width() - 10  # remove padding
        canvas_height = self.canvas.winfo_height() - 10  # remove padding
        if (canvas_width <= 0) or (canvas_height <= 0):
            self.mainwindow.after(
                1000,
                lambda: self.update_plot())
            return

        if show_busy:
            self.start_busy()
        self.updating = True

        thread = Thread(target=perform_plot_update, args=(self, canvas_width, canvas_height, show_busy))
        thread.start()

    def display_updated_plot(self, resized_image, width, height, show_busy):
        self.canvas.delete("all")  # Clear previous content

        # Place the resized image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=resized_image)
        self.canvas.photo = resized_image  # Store a reference to prevent garbage collection

        # Update canvas size
        self.canvas.config(width=width, height=height)

        self.updating = False
        if show_busy:
            self.stop_busy()

    def map_metadata_to_rgb(self, metadata_values):
        """
        Generates a color map for the metadata values.

        :param metadata_values: the metadata values
        :return: the rgb colors
        """
        metadata_values = np.squeeze(metadata_values)
        cmap = plt.get_cmap("viridis")
        norm = Normalize(vmin=np.min(metadata_values), vmax=np.max(metadata_values))
        # Precompute the entire colormap
        colormap = cmap(norm(metadata_values))
        # Get RGB colors for each value
        rgb_colors = colormap[:, :, :3]  # Extract RGB channels
        return rgb_colors

    def state_to_session(self):
        """
        Transfers the current state in the UI to the session manager.
        """
        self.session.scale_r = self.state_scale_r.get()
        self.session.scale_g = self.state_scale_g.get()
        self.session.scale_b = self.state_scale_b.get()
        self.session.opacity = self.state_opacity.get()

    def session_to_state(self):
        """
        Transfers the session data to the UI.
        """
        self.state_scale_r.set(self.session.scale_r)
        self.on_scale_r_changed(None)
        self.state_scale_g.set(self.session.scale_g)
        self.on_scale_g_changed(None)
        self.state_scale_b.set(self.session.scale_b)
        self.on_scale_b_changed(None)
        self.state_opacity.set(self.session.opacity)
        self.on_scale_opacity_changed(None)
        self.select_metadata_key(self.session.selected_metadata_key)

    def run(self):
        self.mainwindow.mainloop()

    def on_listbox_samples_select(self, event=None):
        if len(self.listbox_samples.curselection()) == 1:
            sample = self.listbox_samples.get([self.listbox_samples.curselection()[0]])
            self.load_sample(sample)

    def on_listbox_regions_select(self, event=None):
        if len(self.listbox_regions.curselection()) == 1:
            region = self.listbox_regions.get([self.listbox_regions.curselection()[0]])
            self.load_region(region)

    def on_metadata_select(self, event):
        self.combined_image = None
        self.session.selected_metadata_key = self.combobox_metadata.get()
        if (self.stored_happy_data is not None) and (self.session.selected_metadata_key is not None):
            if "data" in self.stored_happy_data[0].metadata_dict[self.session.selected_metadata_key]:
                metadata_values = self.stored_happy_data[0].metadata_dict[self.session.selected_metadata_key]["data"]
                self.metadata_values = np.squeeze(metadata_values)
                self.metadata_rgb_colors = self.map_metadata_to_rgb(self.metadata_values)
            else:
                self.log(str(self.stored_happy_data[0].metadata_dict[self.session.selected_metadata_key]))
        self.update_plot()

    def on_window_resize(self, event):
        self.update_plot(show_busy=False)

    def on_file_open_dir_click(self, event=None):
        sel_dir = fd.askdirectory(
            title="Select base directory",
            initialdir=self.session.current_dir,
            parent=self.mainwindow)
        if sel_dir is None:
            return

        self.load_dir(sel_dir)

    def on_file_export_image_click(self, event=None):
        if self.rgb_image is None:
            messagebox.showerror("Error", "No image to export!")
            return

        fname = self.session.current_sample + "-" + self.session.current_region + ".png"
        filetypes = (
            ('PNG files', '*.png'),
            ('All files', '*.*')
        )
        filename = fd.asksaveasfilename(
            title="Save image",
            initialdir=self.session.last_export_dir,
            initialfile=fname,
            filetypes=filetypes)
        # when canceling the dialog, an emtpy tuple is returned
        if isinstance(filename, tuple):
            filename = None
        if (filename is None) or (filename == ""):
            return

        self.session.last_export_dir = os.path.dirname(filename)
        if self.combined_image is not None:
            self.combined_image.save(filename)
        elif self.rgb_image is not None:
            self.rgb_image.save(filename)
        else:
            messagebox.showerror("Error", "No image to save?")

    def on_file_close_click(self, event=None):
        self.state_to_session()
        self.session.save()
        self.mainwindow.quit()

    def on_view_normalization_click(self, event=None):
        norm = ttkSimpleDialog.askstring("Normalization", "Please enter command-line for new normalization:",
                                         initialvalue=self.normalization_cmdline, parent=self.mainwindow)
        if (norm is None) or (len(norm) == 0):
            return
        try:
            AbstractNormalization.parse_normalization(norm)
            self.set_normalization(norm)
        except:
            messagebox.showerror("Error", "Failed to parse normalization: %s\n%s" % (norm, traceback.format_exc()))

    def on_view_zoom_click(self, event=None):
        if (event is not None) and (event.startswith("command_view_zoom_")):
            try:
                zoom = int(event.replace("command_view_zoom_", ""))
                self.session.zoom = zoom
                self.update_plot(show_busy=False)
            except:
                self.log("Failed to extract zoom from: %s" % event)

    def on_view_zoom_fit(self, event=None):
        self.session.zoom = -1
        self.update_plot(show_busy=False)

    def on_view_zoom_custom(self, event=None):
        curr_zoom = self.session.zoom
        if curr_zoom <= 0:
            curr_zoom = -1
        new_zoom = ttkSimpleDialog.askinteger("Zoom", "Please enter new zoom (in %; -1 for best fit):",
                                              initialvalue=curr_zoom,
                                              parent=self.mainwindow)
        if new_zoom is not None:
            if new_zoom <= 0:
                new_zoom = -1
            self.session.zoom = new_zoom
            self.update_plot(show_busy=False)

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

    def on_scale_opacity_changed(self, scale_value):
        self.combined_image = None
        self.update_plot(show_busy=False)

    def on_scale_r_changed(self, scale_value):
        self.label_r_value.configure(text=str(self.state_scale_r.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot(show_busy=False)

    def on_scale_g_changed(self, scale_value):
        self.label_g_value.configure(text=str(self.state_scale_g.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot(show_busy=False)

    def on_scale_b_changed(self, scale_value):
        self.label_b_value.configure(text=str(self.state_scale_b.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot(show_busy=False)

    def on_label_r_click(self, event=None):
        channel_range = ""
        if self.get_num_bands() > 0:
            channel_range = " (0-%d)" % (self.get_num_bands() - 1)
        new_channel = ttkSimpleDialog.askinteger(
            title="Red channel",
            prompt="Please enter the channel to use as Red%s:" % channel_range,
            initialvalue=self.state_scale_r.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_r.set(new_channel)

    def on_label_g_click(self, event=None):
        channel_range = ""
        if self.get_num_bands() > 0:
            channel_range = " (0-%d)" % (self.get_num_bands() - 1)
        new_channel = ttkSimpleDialog.askinteger(
            title="Green channel",
            prompt="Please enter the channel to use as Green%s:" % channel_range,
            initialvalue=self.state_scale_g.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_g.set(new_channel)

    def on_label_b_click(self, event=None):
        channel_range = ""
        if self.get_num_bands() > 0:
            channel_range = " (0-%d)" % (self.get_num_bands() - 1)
        new_channel = ttkSimpleDialog.askinteger(
            title="Blue channel",
            prompt="Please enter the channel to use as Blue%s:" % channel_range,
            initialvalue=self.state_scale_b.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_b.set(new_channel)

    def get_num_bands(self):
        """
        Returns the number of bands available.

        :return: the number of bands, 0 if no data present
        :rtype: int
        """
        if self.stored_happy_data is None:
            return 0
        else:
            return self.stored_happy_data[0].data.shape[2]

    def set_normalization(self, cmdline):
        """
        Sets the normalization to use.

        :param cmdline: the commandline of the normalization to use
        :type cmdline: str
        """
        try:
            self.normalization = AbstractNormalization.parse_normalization(cmdline)
            self.normalization_cmdline = cmdline
        except:
            logger.exception("Failed to parse normalization cmdline: %s" % cmdline)
            self.normalization = SimpleNormalization()
            self.normalization_cmdline = SimpleNormalization().name()



def main():
    init_app()
    parser = argparse.ArgumentParser(
        description="Viewer for HAPPy data folder structures.",
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--base_folder", help="Base folder to display", default=None, required=False)
    parser.add_argument("--sample", help="The sample to load", default=None, required=False)
    parser.add_argument("--region", help="The region to load", default=None, required=False)
    parser.add_argument("-r", "--scale_r", metavar="INT", help="the wave length to use for the red channel", default=None, type=int, required=False)
    parser.add_argument("-g", "--scale_g", metavar="INT", help="the wave length to use for the green channel", default=None, type=int, required=False)
    parser.add_argument("-b", "--scale_b", metavar="INT", help="the wave length to use for the blue channel", default=None, type=int, required=False)
    parser.add_argument("-o", "--opacity", metavar="INT", help="the opacity to use (0-100)", default=None, type=int, required=False)
    parser.add_argument("--listbox_selectbackground", type=str, help="The background color to use for selected items in listboxes", default="#4a6984", required=False)
    parser.add_argument("--listbox_selectforeground", type=str, help="The foreground color to use for selected items in listboxes", default="#ffffff", required=False)
    parser.add_argument("--normalization", metavar="PLUGIN", help="the normalization plugin and its options to use", default=SimpleNormalization().name(), type=str, required=False)
    parser.add_argument("--zoom", metavar="PERCENT", help="the initial zoom to use (%%) or -1 for automatic fit", default=-1, type=int, required=False)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args()
    set_logging_level(logger, parsed.logging_level)
    app = ViewerApp()

    # display settings
    app.set_listbox_selectbackground(parsed.listbox_selectbackground)
    app.set_listbox_selectforeground(parsed.listbox_selectforeground)
    app.set_normalization(parsed.normalization)

    # override session data
    app.session.load()
    if parsed.base_folder is not None:
        app.session.current_dir = parsed.base_folder
    if parsed.sample is not None:
        app.session.current_sample = parsed.sample
    if parsed.region is not None:
        app.session.current_region = parsed.region
    if parsed.scale_r is not None:
        app.session.scale_r = parsed.scale_r
    if parsed.scale_g is not None:
        app.session.scale_r = parsed.scale_g
    if parsed.scale_b is not None:
        app.session.scale_r = parsed.scale_b
    if parsed.opacity is not None:
        app.session.opacity = parsed.opacity
    if parsed.zoom is not None:
        app.session.zoom = parsed.zoom
    app.session_to_state()
    try:
        app.load(app.session.current_dir, app.session.current_sample,
                 app.session.current_region, app.session.selected_metadata_key)
    except:
        pass

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


if __name__ == "__main__":
    main()
