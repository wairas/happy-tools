import abc
import json
import os

from happy.base.config import get_config_dir


class AbstractSessionManager(abc.ABC):
    """
    For managing session parameters.
    """

    def __init__(self, log_method=None):
        """
        Initializes the manager.

        :param log_method: the log method to use (only takes a single str arg, the message)
        """
        super().__init__()
        self.log_method = log_method

    def log(self, msg):
        """
        For logging messages.

        :param msg: the message to output
        :type msg: str
        """
        if self.log_method is not None:
            self.log_method(msg)
        else:
            print(msg)

    def get_default_config_name(self):
        """
        Returns the filename (no path) of the session config file.

        :return: the name
        :rtype: str
        """
        raise NotImplementedError()

    def get_default_config_path(self):
        """
        Returns the default config file location.

        :return: the default config file
        :rtype: str
        """
        return os.path.join(get_config_dir(), self.get_default_config_name())

    def get_properties(self):
        """
        Returns the list of properties of the session manager to save/load.

        :return: the list of property names
        :rtype: list
        """
        raise NotImplementedError()

    def save(self, path=None):
        """
        Saves the session (as json).

        :param path: the file to save to, uses a default location when None
        :type path: str
        """
        data = dict()
        for p in self.get_properties():
            data[p] = getattr(self, p)

        if path is None:
            path = self.get_default_config_path()

        self.log("Saving session: %s" % path)
        with open(path, "w") as fp:
            json.dump(data, fp, indent=4)

    def load(self, path=None):
        """
        Loads the session (from json).

        :param path: the file to load from, uses default location when None
        :type path: str
        """
        if path is None:
            path = self.get_default_config_path()
            # does not exist (yet)?
            if not os.path.exists(path):
                return

        self.log("Loading session: %s" % path)
        with open(path, "r") as fp:
            data = json.load(fp)

        for p in self.get_properties():
            if p in data:
                setattr(self, p, data[p])
