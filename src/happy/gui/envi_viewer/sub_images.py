#!/usr/bin/python3
import pathlib
import pygubu
import re
from tkinter import messagebox
from typing import Optional, Dict
from happy.gui import ToolTip
from happy.writers import output_pattern_help


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "sub_images.ui"

KEY_OUTPUT_DIR = "output_dir"
KEY_LABEL_REGEXP = "label_regexp"
KEY_OUTPUT_FORMAT = "output_format"
KEY_RAW_SPECTRA = "raw_spectra"
KEY_OUTPUT_PATTERN = "output_pattern"


class SubImagesDialog:
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
        self.dialog_sub_images = builder.get_object("dialog_sub_images", master)
        builder.connect_callbacks(self)

        # other widgets
        self.pathchooser_output_dir = builder.get_object("pathchooser_output_dir", self.dialog_sub_images)
        self.entry_regexp = builder.get_object("entry_regexp", self.dialog_sub_images)
        self.entry_output_pattern = builder.get_object("entry_output_pattern", self.dialog_sub_images)
        self.combobox_output_format = builder.get_object("combobox_output_format", self.dialog_sub_images)
        self.button_ok = builder.get_object("button_ok", self.dialog_sub_images)
        self.button_cancel = builder.get_object("button_cancel", self.dialog_sub_images)

        # states
        self.state_entry_regexp = None
        self.state_output_pattern = None
        self.state_raw = None
        builder.import_variables(self)

        # tooltips
        self.tooltip_output_pattner = ToolTip(self.entry_output_pattern, text=output_pattern_help(), wraplength=250)

        # others
        self.accepted = None

    def validate(self) -> Optional[str]:
        """
        Validates the input.

        :return: None if validation passed, otherwise error message
        :rtype: str
        """
        params = self.parameters

        if len(params[KEY_OUTPUT_DIR]) == 0:
            return "No output directory selected!"

        if (params[KEY_OUTPUT_FORMAT] is None) or (len(params[KEY_OUTPUT_FORMAT]) == 0):
            return "No output format selected!"

        if len(params[KEY_LABEL_REGEXP]) > 0:
            try:
                re.compile(params[KEY_LABEL_REGEXP])
            except:
                return "Invalid label regexp!"

        return None

    @property
    def parameters(self) -> Dict:
        """
        Returns the chosen parameters as dictionary.
        :return: the dictionary of parameters
        :rtype: dict
        """
        return {
            KEY_OUTPUT_DIR: self.pathchooser_output_dir.cget("path"),
            KEY_LABEL_REGEXP: self.state_entry_regexp.get(),
            KEY_OUTPUT_FORMAT: self.combobox_output_format.get(),
            KEY_RAW_SPECTRA: self.state_entry_regexp.get() == 1,
            KEY_OUTPUT_PATTERN: self.state_output_pattern.get(),
        }

    @parameters.setter
    def parameters(self, params: Dict):
        """
        Sets the initial parameters to display.

        :param params: the parameters
        :type params: dict
        """
        if (KEY_OUTPUT_DIR in params) and (params[KEY_OUTPUT_DIR] is not None):
            self.pathchooser_output_dir.configure(path=params[KEY_OUTPUT_DIR])
        else:
            self.pathchooser_output_dir.configure(path=".")
        if (KEY_LABEL_REGEXP in params) and (params[KEY_LABEL_REGEXP] is not None):
            self.state_entry_regexp.set(params[KEY_LABEL_REGEXP])
        else:
            self.entry_regexp.set("")
        if (KEY_OUTPUT_FORMAT in params) and (params[KEY_OUTPUT_FORMAT] is not None):
            self.combobox_output_format.set(params[KEY_OUTPUT_FORMAT])
        else:
            self.combobox_output_format.set("happy")
        if (KEY_RAW_SPECTRA in params) and (params[KEY_RAW_SPECTRA] is not None):
            self.state_raw.set(1 if params[KEY_RAW_SPECTRA] else 0)
        else:
            self.state_raw.set(0)
        if (KEY_OUTPUT_PATTERN in params) and (params[KEY_OUTPUT_PATTERN] is not None):
            self.state_output_pattern.set(params[KEY_OUTPUT_PATTERN])
        else:
            self.state_output_pattern.set("")

    def show(self, params: Optional[Dict]):
        """
        Shows the dialog with the parameters.
        """
        if params is not None:
            self.parameters = params
        self.dialog_sub_images.run()
        self.master.wait_window(self.dialog_sub_images.toplevel)

    def on_button_cancel_click(self, event=None):
        self.accepted = None
        self.dialog_sub_images.close()
        self.dialog_sub_images.destroy()

    def on_button_ok_click(self, event=None):
        msg = self.validate()
        if msg is None:
            self.accepted = self.parameters
            self.dialog_sub_images.close()
            self.dialog_sub_images.destroy()
        else:
            messagebox.showerror("Error", msg)


def show_sub_images_dialog(parent, params: Optional[Dict]) -> Optional[Dict]:
    """
    Shows the sub-images dialog and returns the parameters, None if canceled.

    :param parent: the parent window
    :param params: the initial parameters to display, uses default if None
    :type params: dict or None
    :return: the selected parameters, None if canceled
    :rtype: dict or None
    """
    dlg = SubImagesDialog(parent)
    dlg.show(params)
    return dlg.accepted
