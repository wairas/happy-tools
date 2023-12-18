from dataclasses import dataclass
from typing import Optional


@dataclass
class UndoPoint:

    # the comment for the undo point
    comment: str

    # the undo data
    data: None


class UndoManager:

    def __init__(self, max_undo: int = 100, log_method=None):
        """
        Initializes the undo manager.

        :param max_undo: the maximum number of undos to perform, <= for unlimited
        :type max_undo: int
        :param log_method: the method to use for logging (takes single string)
        """
        self.max_undo = max_undo
        self.log_method = log_method
        self.undos = list()
        self.redos = list()

    def log(self, msg):
        """
        Logs the supplied message.

        :param msg: the message to log
        :type msg: str
        """
        if self.log_method is None:
            print(msg)
        else:
            self.log_method(msg)

    def clear(self):
        """
        Removes all undo/redo points.
        """
        self.undos.clear()
        self.redos.clear()

    def add_undo(self, comment: str, data):
        """
        Adds a new undo point.

        :param comment: the comment for the undo
        :type comment: str
        :param data: the associated data
        """
        undo = UndoPoint(comment=comment, data=data)
        self.undos.append(undo)
        self.log("Added undo: %s" % comment)
        if self.max_undo > 0:
            while len(self.undos) > self.max_undo:
                self.undos.pop(0)

    def can_undo(self) -> bool:
        """
        Checks whether an undo is currently possible.

        :return: True if possible
        :rtype: bool
        """
        return len(self.undos) > 0

    def peek_undo(self) -> Optional[UndoPoint]:
        """
        Returns the most recent undo point, if available, without removing it.

        :return: the undo point, None if not available
        :rtype: UndoPoint
        """
        if len(self.undos) == 0:
            return None
        else:
            return self.undos[-1]

    def undo(self) -> Optional[UndoPoint]:
        """
        Returns the most recent undo point and removes it from the internal list.

        :return: the undo point, None if not available
        :rtype: UndoPoint
        """
        result = None
        if len(self.undos) > 0:
            result = self.undos.pop()
            self.log("Undo: %s" % result.comment)
        return result

    def add_redo(self, comment: str, data):
        """
        Adds a new redo point.

        :param comment: the comment for the undo
        :type comment: str
        :param data: the associated data
        """
        redo = UndoPoint(comment=comment, data=data)
        self.redos.append(redo)
        self.log("Added redo: %s" % comment)
        if self.max_undo > 0:
            while len(self.redos) > self.max_undo:
                self.redos.pop(0)

    def can_redo(self) -> bool:
        """
        Checks whether a redo is currently possible.

        :return: True is possible
        :rtype:
        """
        return len(self.redos) > 0

    def peek_redo(self) -> Optional[UndoPoint]:
        """
        Returns the most recent redo, if available, without removing it.

        :return: the redo point, None if not available
        :rtype: UndoPoint
        """
        if len(self.redos) == 0:
            return None
        else:
            return self.redos[-1]

    def redo(self) -> Optional[UndoPoint]:
        """
        Returns the most recent undo point and removes it from the internal list.

        :return: the undo point, None if not available
        :rtype: UndoPoint
        """
        result = None
        if len(self.redos) > 0:
            result = self.redos.pop()
            self.log("Redo: %s" % result.comment)
        return result
