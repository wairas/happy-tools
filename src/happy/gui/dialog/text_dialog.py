#!/usr/bin/python3
import pathlib
import pygubu
import tkinter as tk

from typing import Optional

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "text_dialog.ui"


class TextDialog:
    def __init__(self, master=None):
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # widgets
        self.dialog_text = builder.get_object("dialog_text", master)
        self.text_content = builder.get_object("text_content", master)

        # callbacks
        builder.connect_callbacks(self)

    def show(self, content: Optional[str]):
        """
        Shows the dialog with the content.
        """
        if content is None:
            content = ""
        self.text_content.delete(1.0, tk.END)
        self.text_content.insert(tk.END, content)
        self.dialog_text.run()
        self.master.wait_window(self.dialog_text.toplevel)

    def on_button_ok_click(self):
        self.dialog_text.close()
        self.dialog_text.destroy()


def show_text_dialog(parent, content: Optional[str]):
    """
    Shows a text dialog with the content.

    :param parent: the parent window
    :param content: the text content to display, can be None
    :type content: str or None
    """
    dlg = TextDialog(parent)
    dlg.show(content)
