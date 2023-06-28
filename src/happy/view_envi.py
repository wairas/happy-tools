import argparse
import traceback
import numpy as np
import spectral.io.envi as envi
import tkinter as tk
from PIL import ImageTk, Image
import random


class Viewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ENVI False Color")

        # Create a frame for controls
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # Create scales for selecting the wavelengths
        # 1. red
        self.red_label = tk.Label(self.controls_frame, text="Red Wavelength:")
        self.red_label.pack(anchor=tk.W)
        self.red_scale = tk.Scale(self.controls_frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.red_scale.pack(anchor=tk.W)
        # 2. green
        self.green_label = tk.Label(self.controls_frame, text="Green Wavelength:")
        self.green_label.pack(anchor=tk.W)
        self.green_scale = tk.Scale(self.controls_frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.green_scale.pack(anchor=tk.W)
        # 3. blue
        self.blue_label = tk.Label(self.controls_frame, text="Blue Wavelength:")
        self.blue_label.pack(anchor=tk.W)
        self.blue_scale = tk.Scale(self.controls_frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.blue_scale.pack(anchor=tk.W)

        # buttons
        self.button_frame = tk.Frame(self.controls_frame)
        self.button_frame.pack(anchor=tk.W, pady=10)

        self.random_button = tk.Button(self.button_frame, text="Random", command=self.select_random_wavelengths)
        self.random_button.pack(side=tk.LEFT, padx=5)

        self.update_button = tk.Button(self.button_frame, text="Update", command=self.update_image)
        self.update_button.pack(side=tk.LEFT, padx=5)

        # initialize members
        self.image_label = None
        self.data = None
        self.photo = None

    def update_image(self):
        """
        Generates a false color image from the loaded data and displays the image.
        """
        # Get the selected wavelengths
        red_wavelength = int(self.red_scale.get())
        green_wavelength = int(self.green_scale.get())
        blue_wavelength = int(self.blue_scale.get())

        # Get the corresponding channels from the data
        red_channel = self.data[:, :, red_wavelength]
        green_channel = self.data[:, :, green_wavelength]
        blue_channel = self.data[:, :, blue_wavelength]

        # Normalize the channels
        red_channel = (red_channel - np.min(red_channel)) / (np.max(red_channel) - np.min(red_channel))
        green_channel = (green_channel - np.min(green_channel)) / (np.max(green_channel) - np.min(green_channel))
        blue_channel = (blue_channel - np.min(blue_channel)) / (np.max(blue_channel) - np.min(blue_channel))

        # Create the false color image
        false_color_image = np.dstack((red_channel, green_channel, blue_channel))

        # Convert the image array to PIL Image format
        image = Image.fromarray((false_color_image * 255).astype(np.uint8))

        self.photo = ImageTk.PhotoImage(image)
        if self.image_label is None:
            self.image_label = tk.Label(self, image=self.photo)
            self.image_label.pack(padx=10, pady=10)
        else:
            self.image_label.configure(image=self.photo)

        self.image_label.image = self.photo

    def select_random_wavelengths(self):
        """
        Randomly selects wavelengths.
        """
        num_bands = self.data.shape[2]
        red_wavelength = random.randint(0, num_bands - 1)
        green_wavelength = random.randint(0, num_bands - 1)
        blue_wavelength = random.randint(0, num_bands - 1)

        # Set the selected wavelengths in the scales
        self.red_scale.set(red_wavelength)
        self.green_scale.set(green_wavelength)
        self.blue_scale.set(blue_wavelength)

    def load_file(self, filename):
        self.data = envi.open(filename).load()
        self.update_image()


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="Display ENVI file in false color.",
        prog="happy-viewer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename', type=str, help='Path to the ENVI file')
    parsed = parser.parse_args(args=args)
    app = Viewer()
    app.load_file(parsed.filename)
    app.mainloop()


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
