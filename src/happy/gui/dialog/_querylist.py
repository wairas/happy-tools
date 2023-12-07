import sys
if sys.version_info.major == 3:
    import tkinter as _tk
    from tkinter import ttk as _ttk
else:
    import Tkinter as _tk
    import ttk as _ttk
from ttkSimpleDialog.ttkSimpleDialog import Dialog


class QueryListDialog(Dialog):
    errormessage = "Not a list item."

    def __init__(self, title, prompt, items,
                 initialvalue=None,
                 parent=None):
        """
        Initializes the dialog.

        Arguments:

            parent -- a parent window (the application window)

            title -- the dialog title

            prompt -- the text prompt

            items -- the list of items to fill the combobox with

            initialvalue -- the initial value to select from the combobox

            parent -- the parent this dialog belongs to
        """
        if (items is None) or (len(items) == 0):
            raise ValueError("List of items cannot be None or empty!")
        if (items is not None) and (initialvalue is not None):
            if initialvalue not in items:
                raise ValueError("Couldn't find '%s' among list items '%s'!" % (initialvalue, "|".join(items)))

        if not parent:
            parent = _tk.Tk()
            parent.withdraw()

        self.prompt = prompt
        self.items = items
        self.initialvalue = initialvalue
        self.combobox = None
        super().__init__(parent, title)

    def destroy(self):
        self.combobox = None
        Dialog.destroy(self)

    def body(self, master):
        w = _ttk.Label(master, text=self.prompt, justify=_tk.LEFT)
        w.grid(row=0, padx=5, sticky=_tk.W)

        self.combobox = _ttk.Combobox(master, name="entry")
        self.combobox.grid(row=1, padx=5, sticky=_tk.W + _tk.E)
        self.combobox['values'] = self.items

        if self.initialvalue is not None:
            self.combobox.set(self.initialvalue)

        return self.combobox

    def validate(self):
        if sys.version_info.major == 3:
            from tkinter import messagebox as tkMessageBox
        else:
            import tkMessageBox

        try:
            result = self.getresult()
        except ValueError:
            tkMessageBox.showwarning(
                "Illegal value",
                self.errormessage + "\nPlease try again",
                parent=self
            )
            return 0

        self.result = result

        return 1

    def getresult(self):
        return self.combobox.get()


def asklist(title, prompt, items, **kw):
    """
    get a list item from the user

    Arguments:

        title -- the dialog title
        prompt -- the label text
        items -- the list items for the combobox
        **kw -- see SimpleDialog class

    Return value is a string
    """
    d = QueryListDialog(title, prompt, items, **kw)
    return d.result
