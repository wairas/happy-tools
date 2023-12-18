from threading import Thread


def monitor_thread(widget, thread, finish_method=None, wait=100):
    """
    For monitoring threads and calling a method after the thread finishes, e.g., for updating the GUI.

    :param widget: the tkinter widget to use for calling the "after" method, e.g., the main window
    :param thread: the thread to monitor
    :type thread: Thread
    :param finish_method: the method to call after the thread finishes, can be None
    :param wait: the time to wait in msec before checking on the thread again
    :type wait: int
    """
    if thread.is_alive():
        # check the thread every X ms
        widget.after(wait, lambda: monitor_thread(widget, thread, finish_method=finish_method, wait=wait))
    else:
        if finish_method is not None:
            finish_method()
