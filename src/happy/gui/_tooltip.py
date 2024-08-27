# based on:
# https://stackoverflow.com/a/36221216/4698227
# License: https://creativecommons.org/licenses/by-sa/3.0/

import tkinter as tk


class ToolTip(object):
    """
    Create a tool tip for the given widget.
    """
    def __init__(self, widget, text='widget info', waittime=500, wraplength=180):
        """
        Initializes the tooltip.

        :param widget: the widget to wrap
        :param text: the text of the tool tip, use newlines to multi-line tool tips
        :type text: str
        :param waittime: the time in milliseconds to wait
        :type waittime: int
        :param wraplength: the width of the tool tip in pixels before wrapping
        :type wraplength: int
        """
        self.waittime = waittime
        self.wraplength = wraplength
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
