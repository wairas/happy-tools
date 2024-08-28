#!/usr/bin/python3
import argparse
import logging
import os
import pathlib
import tkinter as tk
import traceback
import webbrowser
from tkinter import filedialog as fd
from tkinter import messagebox

import pygubu

from happy.base.app import init_app
from happy.console.raw_check.process import OUTPUT_FORMATS, OUTPUT_FORMAT_TEXT, OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_CSV, \
    output_results, locate_capture_dirs, check_dir
from happy.gui.dialog import asklist
from happy.gui.raw_checker import SessionManager, PROPERTIES
from happy.gui import URL_PROJECT, URL_TOOLS, show_busy_cursor, show_normal_cursor

PROG = "happy-raw-checker"

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "checker.ui"

logger = logging.getLogger(PROG)


class CheckerApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # Main widget
        self.mainwindow = builder.get_object("toplevel", master)
        builder.connect_callbacks(self)
        self.mainwindow.iconphoto(False, tk.PhotoImage(file=str(PROJECT_PATH) + '/../../logo.png'))
        self.texbox_output = builder.get_object("texbox_output", master)

        # accelerators are just strings, we need to bind them to actual methods
        # https://tkinterexamples.com/events/keyboard/
        self.mainwindow.bind("<Control-o>", self.on_file_select_dir)
        self.mainwindow.bind("<Control-s>", self.on_file_save_output)
        self.mainwindow.bind("<Control-c>", self.on_edit_copy)
        self.mainwindow.bind("<Alt-x>", self.on_file_exit)

        # other variables
        self.session = SessionManager(log_method=self.log)

    def log(self, msg):
        """
        Prints message on stdout.

        :param msg: the message to log
        :type msg: str
        """
        if msg != "":
            logger.info(msg)

    def on_file_select_dir(self, event=None):
        raw_dir = self.session.raw_dir
        if raw_dir is None:
            raw_dir = "."
        raw_dir = fd.askdirectory(initialdir=raw_dir, parent=self.mainwindow)
        if (raw_dir is None) or (len(raw_dir) == 0):
            return
        self.session.raw_dir = raw_dir
        self.log("Selected dir: %s" % raw_dir)
        self.run_check()

    def on_file_save_output(self, event=None):
        if self.session.raw_dir is None:
            messagebox.showerror("Error", "Please select a directory first to generate a check!")
            return

        if self.session.output_format == OUTPUT_FORMAT_JSON:
            ext = ".json"
            filetypes = (
                ('JSON files', '*' + ext),
                ('All files', '*.*')
            )
        elif self.session.output_format == OUTPUT_FORMAT_CSV:
            ext = ".csv"
            filetypes = (
                ('CSV files', '*' + ext),
                ('All files', '*.*')
            )
        else:
            ext = ".txt"
            filetypes = (
                ('Text files', '*' + ext),
                ('All files', '*.*')
            )
        initial_file = os.path.basename(self.session.raw_dir) + ext
        filename = fd.asksaveasfilename(
            title="Save output",
            initialdir=self.session.last_save_dir,
            initialfile=initial_file,
            filetypes=filetypes)
        if (filename is None) or (len(filename) == 0):
            return

        output = self.texbox_output.get("1.0", "end-1c")
        self.log("Writing output to: %s" % filename)
        with open(filename, "w") as fp:
            fp.write(output)

    def on_file_exit(self, event=None):
        self.session.save()
        self.mainwindow.quit()

    def on_edit_copy(self, event=None):
        self.mainwindow.clipboard_clear()
        self.mainwindow.clipboard_append(self.texbox_output.get("1.0", "end-1c"))

    def on_view_outputformat(self, event=None):
        output_format = asklist("Output format", "Please select the output format",
                                OUTPUT_FORMATS, initialvalue=self.session.output_format)
        if (output_format is None) or (len(output_format) == 0):
            return
        self.session.output_format = output_format
        self.run_check()

    def on_help_project_click(self, event=None):
        webbrowser.open(URL_PROJECT)

    def on_help_tools_click(self, event=None):
        webbrowser.open(URL_TOOLS)

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

    def run_check(self):
        if self.session.raw_dir is None:
            return

        self.start_busy()
        capture_dirs = []
        locate_capture_dirs(self.session.raw_dir, capture_dirs, recursive=True)
        capture_dirs = sorted(capture_dirs)
        self.log("Found # capture dirs: %d" % len(capture_dirs))
        results = []
        for capture_dir in capture_dirs:
            results.append(check_dir(capture_dir))

        # generate output
        output = output_results(results, output_format=self.session.output_format, use_stdout=False, return_results=True)
        if output is None:
            output = "-No output generated-"
        self.texbox_output.delete("1.0", tk.END)
        self.texbox_output.insert(tk.END, output)
        self.stop_busy()

    def run(self):
        self.mainwindow.mainloop()


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    init_app()
    parser = argparse.ArgumentParser(
        description="Raw data checker interface. For sanity checks of raw capture data.",
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--raw_dir", type=str, help="The initial directory", required=False, default=None)
    parser.add_argument("-f", "--output_format", choices=OUTPUT_FORMATS, default=OUTPUT_FORMAT_TEXT, help="The output format to use in the text box.", required=False)
    parsed = parser.parse_args(args=args)
    app = CheckerApp()

    # override session data
    app.session.load()
    for p in PROPERTIES:
        if hasattr(parsed, p):
            value = getattr(parsed, p)
            if value is not None:
                setattr(app.session, p, value)

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
