#!/usr/bin/python3
import pathlib
import pygubu
import tkinter as tk
from PIL import ImageTk


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "image.ui"


class ImageDialog:
    def __init__(self, master):
        """
        Initializes the dialog.

        :param master: the parent for the dialog
        """
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # dialog
        self.dialog_image = builder.get_object("dialog_image", master)
        builder.connect_callbacks(self)

        # other widgets
        self.canvas_image = builder.get_object("canvas_image", self.dialog_image)
        self.button_ok = builder.get_object("button_ok", self.dialog_image)
        self.button_cancel = builder.get_object("button_cancel", self.dialog_image)

    def show(self, image):
        """
        Shows the dialog with the image.
        """
        width, height = image.size
        self.photo_scan = ImageTk.PhotoImage(image=image)
        self.canvas_image.create_image(0, 0, image=self.photo_scan, anchor=tk.NW)
        self.canvas_image.config(width=width, height=height)
        self.canvas_image.configure(scrollregion=(0, 0, width - 2, height - 2))
        self.dialog_image.run()

    def on_cancel_click(self, event=None):
        self.dialog_image.close()

    def on_ok_click(self, event=None):
        self.dialog_image.close()
