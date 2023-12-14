from happy.gui.session import AbstractSessionManager
from happy.console.raw_check.process import OUTPUT_FORMAT_TEXT


PROPERTIES = [
    "raw_dir",
    "output_format",
    "last_save_dir",
]


class SessionManager(AbstractSessionManager):
    """
    For managing the session parameters.
    """

    def __init__(self, log_method=None):
        """
        Initializes the manager.

        :param log_method: the log method to use (only takes a single str arg, the message)
        """
        super().__init__(log_method=log_method)
        self.raw_dir = None
        self.output_format = OUTPUT_FORMAT_TEXT
        self.last_save_dir = "."

    def get_default_config_name(self):
        """
        Returns the filename (no path) of the session config file.

        :return: the name
        :rtype: str
        """
        return "raw_checker.json"

    def get_properties(self):
        """
        Returns the list of properties of the session manager to save/load.

        :return: the list of property names
        :rtype: list
        """
        return PROPERTIES
