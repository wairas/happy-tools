from happy.gui.session import AbstractSessionManager


PROPERTIES = [
    "current_dir",
    "current_sample",
    "current_region",
    "last_export_dir",
    "scale_r",
    "scale_g",
    "scale_b",
    "opacity",
    "selected_metadata_key",
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
        self.current_dir = None
        self.current_sample = None
        self.current_region = None
        self.last_export_dir = "."
        self.scale_r = 0
        self.scale_g = 0
        self.scale_b = 0
        self.opacity = 0
        self.selected_metadata_key = None

    def get_default_config_name(self):
        """
        Returns the filename (no path) of the session config file.

        :return: the name
        :rtype: str
        """
        return "data_viewer.json"

    def get_properties(self):
        """
        Returns the list of properties of the session manager to save/load.

        :return: the list of property names
        :rtype: list
        """
        return PROPERTIES
