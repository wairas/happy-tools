#!/usr/bin/python3
import argparse
import numpy as np
import os
import pathlib
import pygubu
import traceback
import tkinter as tk
import tkinter.ttk as ttk

from PIL import Image, ImageTk
from tkinter import filedialog as fd
from ttkSimpleDialog import ttkSimpleDialog
from happy.readers.happy_reader import HappyReader
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "viewer.ui"


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
        self.listbox_repeats = builder.get_object("listbox_repeats", master)
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
        self.listbox_repeats.bind('<<ListboxSelect>>', self.on_listbox_repeats_select)

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
        self.var_listbox_repeats = None
        builder.import_variables(self)

        # other variables
        self.current_dir = "."
        self.current_sample = None
        self.current_repeat = None
        self.reader = None
        self.updating = False
        self.stored_happy_data = None
        self.rgb_image = None
        self.combined_image = None
        self.metadata_values = None
        self.metadata_rgb_colors = None
        self.selected_metadata_key = None

    def log(self, msg):
        """
        Simply outputs the supplied message.

        :param msg: the logging message to output
        :type msg: str
        """
        print(msg)

    def clear_plot(self):
        """
        Clears any previous plot.
        """
        self.rgb_image = None
        self.combined_image = None
        self.canvas.delete("all")

    def load_dir(self, path):
        """
        Opens the specified directory.

        :param path: the directory to load
        :type path: str
        """
        self.log("dir: %s" % path)
        self.label_dir.configure(text=path)
        self.current_dir = path
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
        if len(samples) > 0:
            self.listbox_samples.selection_set(0)
        self.clear_plot()

    def load_sample(self, sample):
        """
        Loads the specified sample from the current directory.

        :param sample: the sample to load
        :type sample: str
        """
        self.log("sample: %s" % sample)
        self.current_sample = sample
        path = os.path.join(self.current_dir, sample)
        repeats = []
        all_numeric = True
        for f in os.listdir(path):
            if f.startswith("."):
                continue
            full = os.path.join(path, f)
            if os.path.isdir(full):
                repeats.append(f)
                try:
                    int(f)
                except:
                    all_numeric = False
        # all numeric?
        if all_numeric:
            repeats = [int(x) for x in repeats]
            repeats.sort(reverse=True)
            repeats = [str(x) for x in repeats]
        else:
            repeats.sort(reverse=True)
        self.var_listbox_repeats.set(repeats)
        if len(repeats) > 0:
            self.listbox_repeats.selection_set(0)
        self.clear_plot()

    def load_repeat(self, repeat):
        """
        Loads the specified repeat from the current dir and sample.

        :param repeat: the repeat to load
        :type repeat: str
        """
        self.log("repeat: %s" % repeat)
        self.current_repeat = repeat
        self.clear_plot()
        self.load_happy_data()

    def load_happy_data(self):
        """
        Loads the current dir/sample/repeat and displays the image.
        """
        if (self.current_dir is None) or (self.current_sample is None) or (self.current_repeat is None):
            return
        full = os.path.join(self.current_dir, self.current_sample, self.current_repeat)
        if not os.path.exists(full) or not os.path.isdir(full):
            return

        self.updating = True
        self.stored_happy_data = self.reader.load_data(self.current_sample + ":" + self.current_repeat)
        # Extract and store the metadata keys
        if self.stored_happy_data is not None:
            metadata_keys = list(self.stored_happy_data[0].metadata_dict.keys())
            sorted(metadata_keys)
            self.update_metadata_combobox(metadata_keys)  # Call a new method to update the Combobox
            if self.selected_metadata_key is not None:
                metadata_values = self.stored_happy_data[0].metadata_dict[self.selected_metadata_key]["data"]
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
        self.update_plot()

    def update_metadata_combobox(self, metadata_keys):
        """
        Update the values in the metadata combobox.

        :param metadata_keys: the keys to display
        :type metadata_keys: list
        """
        self.combobox_metadata['values'] = metadata_keys
        self.combobox_metadata.set(metadata_keys[0])  # Set the default selection

    def convert_to_rgb(self, happy_data):
        # Extract the hyperspectral data array
        hyperspectral_data = happy_data[0].data

        # Get the values of the R, G, and B channel sliders
        r_slider_value = self.state_scale_r.get()
        g_slider_value = self.state_scale_g.get()
        b_slider_value = self.state_scale_b.get()

        # Use the slider values to select the corresponding channels from the data
        r_band = hyperspectral_data[:, :, r_slider_value]
        g_band = hyperspectral_data[:, :, g_slider_value]
        b_band = hyperspectral_data[:, :, b_slider_value]

        # Normalize each band to [0, 255]
        r_normalized = (r_band - r_band.min()) / (r_band.max() - r_band.min()) * 255
        g_normalized = (g_band - g_band.min()) / (g_band.max() - g_band.min()) * 255
        b_normalized = (b_band - b_band.min()) / (b_band.max() - b_band.min()) * 255

        # Create an RGB image using the normalized bands
        rgb_image = Image.fromarray(np.dstack((r_normalized, g_normalized, b_normalized)).astype(np.uint8))

        return rgb_image

    def update_plot(self):
        if self.updating:
            return
        if self.stored_happy_data is None:
            return
        self.updating = True

        if self.rgb_image is None:
            self.rgb_image = self.convert_to_rgb(self.stored_happy_data)

        rgb_image = self.rgb_image

        if self.selected_metadata_key is not None:
            if self.combined_image is None:
                # Convert metadata RGB colors to a NumPy array
                overlay_image = self.metadata_rgb_colors
                # Apply transparency based on opacity slider value
                overlay_alpha = float(self.scale_opacity.get() / 100)  # Scale to 0-255
                # Convert hyperspectral RGB image to float
                rgb_image_float = np.array(rgb_image).astype(float) / 255.0
                # Combine hyperspectral image with the overlay image
                combined_image = (1.0 - overlay_alpha) * rgb_image_float + (overlay_image * overlay_alpha)
                # Clip values to ensure they are within [0, 1]
                combined_image = np.clip(combined_image, 0, 1)
                # Convert the combined image to uint8
                combined_image_uint8 = (combined_image * 255).astype(np.uint8)
                # Create an Image object from the combined image
                self.combined_image = Image.fromarray(combined_image_uint8)
            rgb_image = self.combined_image

        # Calculate canvas dimensions (only once)
        canvas_width = self.canvas.winfo_width() - 10  # remove padding
        canvas_height = self.canvas.winfo_height() - 10  # remove padding

        # Calculate aspect ratio of the image
        width, height = rgb_image.size
        aspect_ratio = width / height

        # Calculate new dimensions while maintaining aspect ratio
        if canvas_width / aspect_ratio < canvas_height:
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = canvas_height
            new_width = int(new_height * aspect_ratio)

        # Resize the image using PIL
        rgb_image = rgb_image.resize((new_width, new_height), Image.ANTIALIAS)

        # Create a new PhotoImage object from the resized PIL image
        resized_image = ImageTk.PhotoImage(rgb_image)

        self.canvas.delete("all")  # Clear previous content

        # Place the resized image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=resized_image)
        self.canvas.photo = resized_image  # Store a reference to prevent garbage collection

        # Update canvas size
        self.canvas.config(width=new_width, height=new_height)

        self.updating = False

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

    def run(self):
        self.mainwindow.mainloop()

    def on_listbox_samples_select(self, event=None):
        if len(self.listbox_samples.curselection()) == 1:
            sample = self.listbox_samples.get([self.listbox_samples.curselection()[0]])
            self.load_sample(sample)

    def on_listbox_repeats_select(self, event=None):
        if len(self.listbox_repeats.curselection()) == 1:
            repeat = self.listbox_repeats.get([self.listbox_repeats.curselection()[0]])
            self.load_repeat(repeat)

    def on_metadata_select(self, event):
        self.combined_image = None
        self.selected_metadata_key = self.combobox_metadata.get()
        if (self.stored_happy_data is not None) and (self.selected_metadata_key is not None):
            metadata_values = self.stored_happy_data[0].metadata_dict[self.selected_metadata_key]["data"]
            self.metadata_values = np.squeeze(metadata_values)
            self.metadata_rgb_colors = self.map_metadata_to_rgb(self.metadata_values)
        self.update_plot()

    def on_window_resize(self, event):
        self.update_plot()

    def on_file_open_dir_click(self):
        sel_dir = fd.askdirectory(
            title="Select base directory",
            initialdir=self.current_dir)
        if sel_dir is None:
            return

        self.load_dir(sel_dir)

    def on_file_export_image_click(self):
        # TODO
        pass

    def on_file_close_click(self):
        self.mainwindow.quit()

    def on_scale_opacity_changed(self, scale_value):
        self.combined_image = None
        self.update_plot()

    def on_scale_r_changed(self, scale_value):
        self.label_r_value.configure(text=str(self.state_scale_r.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot()

    def on_scale_g_changed(self, scale_value):
        self.label_g_value.configure(text=str(self.state_scale_g.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot()

    def on_scale_b_changed(self, scale_value):
        self.label_b_value.configure(text=str(self.state_scale_b.get()))
        self.rgb_image = None
        self.combined_image = None
        self.update_plot()

    def on_label_r_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Red channel",
            prompt="Please enter the channel to use as Red:",
            initialvalue=self.state_scale_r.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_r.set(new_channel)

    def on_label_g_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Green channel",
            prompt="Please enter the channel to use as Green:",
            initialvalue=self.state_scale_g.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_g.set(new_channel)

    def on_label_b_click(self, event=None):
        new_channel = ttkSimpleDialog.askinteger(
            title="Blue channel",
            prompt="Please enter the channel to use as Blue:",
            initialvalue=self.state_scale_b.get(),
            parent=self.mainwindow)
        if new_channel is not None:
            self.scale_b.set(new_channel)


def main():
    parser = argparse.ArgumentParser(
        description="Viewer for HAPPy data folder structures.",
        prog="happy-data-viewer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--base_folder", help="Base folder to display", default=None, required=False)
    parsed = parser.parse_args()
    app = ViewerApp()
    if parsed.base_folder is not None:
        app.load_dir(parsed.base_folder)
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
