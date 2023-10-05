import argparse
import numpy as np
import tkinter as tk
from tkinter import ttk
import traceback

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from PIL import Image, ImageTk  # Import Image and ImageTk from the PIL library
from happy.readers import HappyReader
from happy.data import SampleIDHandler


class DataViewer:
    def __init__(self, base_folder):
        self.base_folder = base_folder
        self.reader = HappyReader(self.base_folder)
        self.sample_id_handler = SampleIDHandler(self.base_folder)
        self.sample_id = None
        self.subfolder = None
        self.sub_sample_list = None  # Initialize sub_sample_list as an instance variable
        self.canvas = None  # Initialize canvas as an instance variable
        self.resize_after_id = None  # Variable to store after() callback ID
        self.rgb_image = None
        self.updating = False
        self.selected_sample_id = None
        self.stored_happy_data = None
        
        self.channel_slider_frame = None
        self.channel_sliders = []

        self.selected_metadata_key = None
        self.opacity_slider = None
        
        self.metadata_combobox = None
        self.metadata_values = None
        self.metadata_rgb_colors = None

    def on_sample_id_chosen(self, selected_sample_id):
        self.sample_id = selected_sample_id
        sub_sample_ids = self.sample_id_handler.get_all_sub_sample_ids(selected_sample_id)
        if len(sub_sample_ids) == 1:
            self.subfolder = sub_sample_ids[0]
            self.load_happy_data(sub_sample_ids[0])
        else:
            self.show_sub_sample_list(sub_sample_ids)  # Show the sub-sample list

    def show_sub_sample_list(self, sub_sample_ids):
        if not self.sub_sample_list:
            self.sub_sample_list = tk.Listbox(self.root)
            self.sub_sample_list.pack(fill=tk.BOTH, expand=True)

            sub_sample_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.sub_sample_list.yview)
            self.sub_sample_list.config(yscrollcommand=sub_sample_scrollbar.set)
            sub_sample_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            def on_sub_sample_select(evt):
                w = evt.widget
                if w.curselection():
                    index = int(w.curselection()[0])
                    selected_sub_sample = w.get(index)
                    self.subfolder = selected_sub_sample
                    self.load_happy_data(selected_sub_sample)

            self.sub_sample_list.bind('<<ListboxSelect>>', on_sub_sample_select)
        
        # Update the list content
        self.sub_sample_list.delete(0, tk.END)
        for sub_sample_id in sub_sample_ids:
            self.sub_sample_list.insert(tk.END, sub_sample_id)

    def on_slider_change(self, *args):
        if not self.updating:
            self.rgb_image = self.convert_to_rgb(self.stored_happy_data)
            self.update_plot(self.stored_happy_data)
     
    def map_metadata_to_rgb_old(self, metadata_values):
        metadata_values = np.squeeze(metadata_values)
        cmap = plt.get_cmap("viridis")  # Choose a colormap (you can change it)
        norm = Normalize(vmin=np.min(metadata_values), vmax=np.max(metadata_values))
        smap = ScalarMappable(cmap=cmap, norm=norm)

        # Map metadata values to RGB colors
        rgb_colors = [smap.to_rgba(value)[:3] for value in metadata_values.flatten()]
        return np.array(rgb_colors).reshape(metadata_values.shape + (3,))

    def map_metadata_to_rgb(self, metadata_values):
        metadata_values = np.squeeze(metadata_values)
        cmap = plt.get_cmap("viridis")
        norm = Normalize(vmin=np.min(metadata_values), vmax=np.max(metadata_values))
        
        # Precompute the entire colormap
        colormap = cmap(norm(metadata_values))

        # Get RGB colors for each value
        rgb_colors = colormap[:, :, :3]  # Extract RGB channels

        return rgb_colors

    def update_plot(self, happy_data):
        if self.updating:
            return
        if self.stored_happy_data is None:
            return
        self.updating = True
        #print("update")
        # Convert the hyperspectral data to an RGB image
        # Get slider values for each channel
        #slider_values = [slider.get() for slider in self.channel_sliders]
        if self.rgb_image is None:
            self.rgb_image = self.convert_to_rgb(self.stored_happy_data)

        rgb_image = self.rgb_image
        
        if self.selected_metadata_key is not None:
            #metadata_values = self.stored_happy_data[0].metadata_dict[self.selected_metadata_key]["data"]
            #metadata_rgb_colors = self.map_metadata_to_rgb(metadata_values)

            # Convert metadata RGB colors to a NumPy array
            overlay_image =self.metadata_rgb_colors
            #print(f"overlay_image dimensions: {overlay_image.shape}")
            #print(f"overlay_image min value: {np.min(overlay_image)}")
            #print(f"overlay_image max value: {np.max(overlay_image)}")
            #print(f"overlay_image data type: {overlay_image.dtype}")

            # Apply transparency based on opacity slider value
            overlay_alpha = float(self.opacity_slider.get() / 100)  # Scale to 0-255
            #print(overlay_alpha)
            #overlay = np.zeros_like(metadata_values, dtype=np.uint8)
            #overlay[:, :] = overlay_alpha

            # Expand overlay dimensions to match hyperspectral data
            #overlay_rgb = np.repeat(overlay[:, :, np.newaxis], 3, axis=2)
            #overlay_rgb = np.squeeze(overlay_rgb)

            # Convert hyperspectral RGB image to float
            rgb_image_float = np.array(rgb_image).astype(float) / 255.0
            #print(f"rgb_image_float data type: {rgb_image_float.dtype}")
            
            #print(f"overlay_rgb:{overlay_rgb.shape} overlay_image:{overlay_image.shape} rgb_image_float{rgb_image_float.shape}")
            
            # Combine hyperspectral image with the overlay image
            #combined_image = (1 - overlay_rgb / 255.0) * rgb_image_float + (overlay_image)
            #combined_image = (1 - overlay_rgb / 255.0) * rgb_image_float + (overlay_image * (overlay_alpha / 255.0))
            combined_image = (1.0 - overlay_alpha) * rgb_image_float + (overlay_image * overlay_alpha)

            # Clip values to ensure they are within [0, 1]
            combined_image = np.clip(combined_image, 0, 1)

            # Convert the combined image to uint8
            combined_image_uint8 = (combined_image * 255).astype(np.uint8)

            # Create an Image object from the combined image
            rgb_image = Image.fromarray(combined_image_uint8)


            # Create an Image object from the combined image
        #combined_image = Image.fromarray(combined_image)

        # Calculate canvas dimensions (only once)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

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

        if self.canvas:
            self.canvas.delete("all")  # Clear previous content

        # Place the resized image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=resized_image)
        self.canvas.photo = resized_image  # Store a reference to prevent garbage collection

        # Update canvas size
        self.canvas.config(width=new_width, height=new_height)
        #print("update end")
        self.updating = False

    def convert_to_rgb(self, happy_data):
        # Extract the hyperspectral data array
        hyperspectral_data = happy_data[0].data

        # Get the values of the R, G, and B channel sliders
        r_slider_value = self.channel_sliders[0].get()
        g_slider_value = self.channel_sliders[1].get()
        b_slider_value = self.channel_sliders[2].get()

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

    def update_metadata_combobox(self, metadata_keys):
        # Update the values in the metadata Combobox
        self.metadata_combobox['values'] = metadata_keys
        self.metadata_combobox.set(metadata_keys[0])  # Set the default selection

    # ... Rest of the methods remain the same
    def load_happy_data(self, selected_sub_sample):
        if self.subfolder:
            self.updating = True  # Prevent further updates during loading
            #sample_id = self.sample_id.split(":")[0]  # Extract the main sample ID
            self.stored_happy_data = self.reader.load_data(self.sample_id+":"+selected_sub_sample)
            # Extract and store the metadata keys
            if self.stored_happy_data:
                metadata_keys = list(self.stored_happy_data[0].metadata_dict.keys())
                self.update_metadata_combobox(metadata_keys)  # Call a new method to update the Combobox
                if self.selected_metadata_key is not None:
                    metadata_values = self.stored_happy_data[0].metadata_dict[self.selected_metadata_key]["data"]
                    self.metadata_values = np.squeeze(metadata_values)
                    self.metadata_rgb_colors = self.map_metadata_to_rgb(self.metadata_values)


            print("Loaded HappyData:", self.stored_happy_data)
            self.rgb_image = None
            #num_channels = len(self.stored_happy_data[0].data[0, 0, :])
            num_channels = len(self.stored_happy_data[0].data[0, 0, :])
        
            # Update the range of existing sliders
            for slider in self.channel_sliders:
                slider.config(from_=0, to=num_channels - 1)  # Update the 'to' value

            # Continue with loading and displaying HappyData...
            self.updating = False  # Allow updates after loading
            self.update_plot(self.stored_happy_data)

    # ... Rest of the create_gui method ...

    def add_channel_sliders(self, num_channels):
        # Clear existing sliders
        for slider in self.channel_sliders:
            slider.destroy()

        self.channel_sliders = []

        # Add sliders for R, G, B channels
        for channel_index in range(num_channels):
            slider = tk.Scale(self.channel_slider_frame, from_=0, to=255, orient=tk.HORIZONTAL)#, label=f"Channel {channel_index}")
            slider.pack(side=tk.TOP, pady=5)  # Arrange sliders vertically with padding
            #slider.bind("<Motion>", self.plot)
            #slider.bind("<ButtonRelease-1>", self.on_slider_change)
            slider.bind("<Motion>", self.on_slider_change)
            self.channel_sliders.append(slider)
            
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("HappyData Viewer")
        self.root.geometry("800x600")  # Set initial window size

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        sample_id_frame = tk.Frame(main_frame)
        sample_id_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=5, sticky="nsew")

        sample_id_var = tk.StringVar(value=self.sample_id_handler.get_all_sample_ids())
        self.sample_id_list = tk.Listbox(sample_id_frame, listvariable=sample_id_var)
        self.sample_id_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar1 = tk.Scrollbar(sample_id_frame, orient=tk.VERTICAL, command=self.sample_id_list.yview)
        self.sample_id_list.config(yscrollcommand=scrollbar1.set)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)

        self.sample_id_list.bind('<<ListboxSelect>>', self.on_sample_id_select)

        metadata_frame = tk.Frame(main_frame)
        metadata_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        #metadata_label = tk.Label(metadata_frame, text="Select Metadata Key:")
        #metadata_label.pack(side=tk.LEFT, padx=5)
        
        self.metadata_combobox = ttk.Combobox(metadata_frame, state="readonly")
        self.metadata_combobox.pack(side=tk.LEFT, padx=5)
        
        def on_metadata_select(event):
            self.selected_metadata_key = self.metadata_combobox.get()
            if self.stored_happy_data and self.selected_metadata_key:
                metadata_values = self.stored_happy_data[0].metadata_dict[self.selected_metadata_key]["data"]
                self.metadata_values = np.squeeze(metadata_values)
                self.metadata_rgb_colors = self.map_metadata_to_rgb(self.metadata_values)

            self.update_plot(self.stored_happy_data)
            
        self.metadata_combobox.bind("<<ComboboxSelected>>", on_metadata_select)

        opacity_frame = tk.Frame(main_frame)
        opacity_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        #opacity_label = tk.Label(opacity_frame, text="Overlay Opacity:")
        #opacity_label.pack(side=tk.LEFT, padx=5)
        
        self.opacity_slider = tk.Scale(opacity_frame, from_=0, to=100, orient=tk.HORIZONTAL)#, label="Opacity")
        self.opacity_slider.set(100)  # Set initial opacity to 100
        self.opacity_slider.pack(side=tk.LEFT, padx=5)
        self.opacity_slider.bind("<Motion>", self.on_opacity_slider_change)

        sub_sample_frame = tk.Frame(main_frame)
        sub_sample_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky="nsew")

        self.sub_sample_list = tk.Listbox(sub_sample_frame)
        self.sub_sample_list.pack(fill=tk.BOTH, expand=True)
        self.sub_sample_list.bind('<<ListboxSelect>>', self.on_sub_sample_select)

        rgb_sliders_frame = tk.Frame(main_frame)
        rgb_sliders_frame.grid(row=2, column=2, rowspan=2, padx=10, pady=0, sticky="nsew")
        
        self.channel_slider_frame = tk.Frame(rgb_sliders_frame)
        self.channel_slider_frame.pack(fill=tk.BOTH, expand=True)
        self.add_channel_sliders(3)

        canvas_frame = tk.Frame(main_frame)
        canvas_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="nsew")

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(3, weight=1)  # Make the canvas resizable
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Bind window resize event to update_plot
        self.root.bind("<Configure>", self.delayed_resize_event)

        self.root.mainloop()  # Start the main event loop

    def on_opacity_slider_change(self, event):
        if self.stored_happy_data and self.selected_metadata_key:
            self.update_plot(self.stored_happy_data)
        #else:
        #    print("something is none")

    def on_sample_id_select(self, evt):
            w = evt.widget
            if w.curselection():
                index = int(w.curselection()[0])
                self.selected_sample_id = w.get(index)
                self.on_sample_id_chosen(self.selected_sample_id)

    def on_sub_sample_select(self, evt):
            w = evt.widget
            if w.curselection():
                index = int(w.curselection()[0])
                selected_sub_sample = w.get(index)
                # Remember the selected index in the first listbox
                #sample_id_index = self.sample_id_list.curselection()

                self.subfolder = selected_sub_sample
                self.load_happy_data(selected_sub_sample)

                # Restore the selection in the first listbox
                # Restore the selected item in the first listbox
                if self.selected_sample_id:
                    sample_id_index = self.sample_id_list.get(0, tk.END).index(self.selected_sample_id)
                    self.sample_id_list.selection_clear(0, tk.END)
                    self.sample_id_list.selection_set(sample_id_index)

    def delayed_resize_event(self, event):
        # Handle window resize event with a delay
        #print("delay resize")
        if self.resize_after_id:
            self.root.after_cancel(self.resize_after_id)
        self.resize_after_id = self.root.after(1, self.update_plot, self.stored_happy_data)

    def resize_event(self, event):
        # Handle window resize event
        # Handle window resize event
        #print("resize event")
        if self.stored_happy_data:
            self.update_plot(self.stored_happy_data)


def main():
    parser = argparse.ArgumentParser(
        description="Viewer for Happy data folder structures.",
        prog="happy-data-viewer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("base_folder", help="Base folder for HappyReader")
    args = parser.parse_args()
    app = DataViewer(args.base_folder)
    app.create_gui()


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
