def show_busy_cursor(widget):
    """
    Displays the hourglass cursor for the widget, e.g., the main window.
    https://www.tcl.tk/man/tcl8.4/TkCmd/cursors.html
    """
    widget.config(cursor="watch")
    widget.update()


def show_normal_cursor(widget):
    """
    Displays the normal cursor for the widget, e.g., the main window.
    """
    widget.config(cursor="")
    widget.update()
