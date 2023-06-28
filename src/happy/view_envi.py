import sys
import argparse
import numpy as np
import spectral.io.envi as envi
import tkinter as tk
from PIL import ImageTk, Image
import random

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Display ENVI file in false color.')
parser.add_argument('filename', type=str, help='Path to the ENVI file')
args = parser.parse_args()

# Check if the filename was provided as a command line argument
if not args.filename:
    print("Please provide the filename as a command line argument.")
    sys.exit(1)

filename = args.filename

# Load ENVI file data
data = envi.open(filename).load()

# Create a Tkinter window
window = tk.Tk()
window.title("ENVI False Color")

# Create a frame for controls
controls_frame = tk.Frame(window)
controls_frame.pack(side=tk.LEFT, padx=10, pady=10)

image_label = None


# Function to update the false color image
def update_image():
    global image_label, photo
    # Get the selected wavelengths
    red_wavelength = int(red_scale.get())
    green_wavelength = int(green_scale.get())
    blue_wavelength = int(blue_scale.get())

    # Get the corresponding channels from the data
    red_channel = data[:, :, red_wavelength]
    green_channel = data[:, :, green_wavelength]
    blue_channel = data[:, :, blue_wavelength]

    # Normalize the channels
    red_channel = (red_channel - np.min(red_channel)) / (np.max(red_channel) - np.min(red_channel))
    green_channel = (green_channel - np.min(green_channel)) / (np.max(green_channel) - np.min(green_channel))
    blue_channel = (blue_channel - np.min(blue_channel)) / (np.max(blue_channel) - np.min(blue_channel))

    # Create the false color image
    false_color_image = np.dstack((red_channel, green_channel, blue_channel))

    # Convert the image array to PIL Image format
    image = Image.fromarray((false_color_image * 255).astype(np.uint8))

    photo = ImageTk.PhotoImage(image)
    if image_label is None:
        image_label = tk.Label(window, image=photo)
        image_label.pack(padx=10, pady=10)
    else:
        image_label.configure(image=photo)

    image_label.image = photo


# Function to select random wavelengths
def select_random_wavelengths():
    num_bands = data.shape[2]
    red_wavelength = random.randint(0, num_bands - 1)
    green_wavelength = random.randint(0, num_bands - 1)
    blue_wavelength = random.randint(0, num_bands - 1)

    # Set the selected wavelengths in the scales
    red_scale.set(red_wavelength)
    green_scale.set(green_wavelength)
    blue_scale.set(blue_wavelength)


# Create scales for selecting the wavelengths
red_label = tk.Label(controls_frame, text="Red Wavelength:")
red_label.pack(anchor=tk.W)
red_scale = tk.Scale(controls_frame, from_=0, to=data.shape[2] - 1, orient=tk.HORIZONTAL)
red_scale.pack(anchor=tk.W)

green_label = tk.Label(controls_frame, text="Green Wavelength:")
green_label.pack(anchor=tk.W)
green_scale = tk.Scale(controls_frame, from_=0, to=data.shape[2] - 1, orient=tk.HORIZONTAL)
green_scale.pack(anchor=tk.W)

blue_label = tk.Label(controls_frame, text="Blue Wavelength:")
blue_label.pack(anchor=tk.W)
blue_scale = tk.Scale(controls_frame, from_=0, to=data.shape[2] - 1, orient=tk.HORIZONTAL)
blue_scale.pack(anchor=tk.W)

button_frame = tk.Frame(controls_frame)
button_frame.pack(anchor=tk.W, pady=10)

random_button = tk.Button(button_frame, text="Random", command=select_random_wavelengths)
random_button.pack(side=tk.LEFT, padx=5)
update_button = tk.Button(button_frame, text="Update", command=update_image)
update_button.pack(side=tk.LEFT, padx=5)

# Create an initial false color image
update_image()

# Start the Tkinter event loop
window.mainloop()
