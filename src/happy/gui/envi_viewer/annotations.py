#!/usr/bin/python3
import pathlib
from tkinter import messagebox

import pygubu

from ttkSimpleDialog import ttkSimpleDialog
from happy.data.annotations import ContoursManager
from happy.gui.dialog import asklist


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "annotations.ui"


class AnnotationsDialog:
    def __init__(self, master, contours_manager, width, height, predefined_labels=None):
        """
        Initializes the dialog.

        :param master: the parent for the dialog
        :param contours_manager: the manager for the contours
        :type contours_manager: ContoursManager
        :param width: the width of the image
        :type width: int
        :param height: the height of the image
        :type height: int
        :param predefined_labels: the list of predefined labels, None if freefrom
        :type predefined_labels: list
        """
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        # dialog
        self.dialog_annotations = builder.get_object("dialog_annotations", master)
        builder.connect_callbacks(self)

        # other widgets
        self.treeview_annotations = builder.get_object("treeview_annotations", self.dialog_annotations)
        self.button_change_label = builder.get_object("button_change_label", self.dialog_annotations)
        self.button_delete = builder.get_object("button_delete", self.dialog_annotations)
        self.button_ok = builder.get_object("button_ok", self.dialog_annotations)
        self.button_cancel = builder.get_object("button_cancel", self.dialog_annotations)

        # other variables
        self.annotations_norm = contours_manager.to_list()
        self.annotations_abs = contours_manager.to_list_absolute(width, height)
        self.annotations_deleted = []
        self.annotations_changed = []
        self.predefined_labels = predefined_labels
        for i, contour in enumerate(self.annotations_abs):
            bbox = contour.bbox()
            self.treeview_annotations.insert(
                parent='', index='end', iid=i, text=(i + 1),
                values=(bbox.left, bbox.top, bbox.right - bbox.left, bbox.bottom - bbox.top, contour.label))
        self.on_annotations_updated = None

    def show(self, on_annotations_updated):
        """
        Shows the dialog with the annotations.

        :param on_annotations_updated: the method to call (changed/list, deleted/list) when the dialog gets accpeted
        """
        self.on_annotations_updated = on_annotations_updated
        self.dialog_annotations.run()

    def on_change_label_click(self, event=None):
        items = self.treeview_annotations.selection()
        if len(items) == 0:
            messagebox.showerror("Error", "Please select annotations first!")
            return

        if len(items) == 1:
            text = "Please enter the new label:"
        else:
            text = "Please enter the new label for %d annotations:" % len(items)
        labels = set()
        for item in items:
            index = int(item)
            if self.annotations_norm[index].has_label():
                labels.add(self.annotations_norm[index].label)
        labels = list(labels)
        if self.predefined_labels is not None:
            if len(labels) == 1:
                label = labels[0]
            else:
                label = self.predefined_labels[0]
            new_label = asklist(
                title="Object label",
                prompt=text,
                items=self.predefined_labels,
                initialvalue=label,
                parent=self.master)
        else:
            new_label = ttkSimpleDialog.askstring(
                title="Object label",
                prompt=text,
                initialvalue="" if (len(labels) != 1) else labels[0],
                parent=self.master)
        # update label
        if new_label is not None:
            for item in items:
                index = int(item)
                self.annotations_norm[index].label = new_label
                self.annotations_abs[index].label = new_label
                if self.annotations_norm[index] not in self.annotations_changed:
                    self.annotations_changed.append(self.annotations_norm[index])
                self.treeview_annotations.set(item, "col_label", new_label)

    def on_delete_click(self, event=None):
        items = self.treeview_annotations.selection()
        if len(items) == 0:
            messagebox.showerror("Error", "Please select annotations first!")
            return

        for item in items:
            index = int(item)
            self.annotations_deleted.append(self.annotations_norm[index])
            self.treeview_annotations.delete(item)
            if self.annotations_norm[index] in self.annotations_changed:
                self.annotations_changed.remove(self.annotations_norm[index])

    def on_cancel_click(self, event=None):
        self.dialog_annotations.close()

    def on_ok_click(self, event=None):
        self.dialog_annotations.close()
        self.on_annotations_updated(self.annotations_changed, self.annotations_deleted)
