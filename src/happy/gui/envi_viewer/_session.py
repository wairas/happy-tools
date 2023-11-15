from happy.gui.session import AbstractSessionManager


PROPERTIES = [
    "autodetect_channels",
    "keep_aspectratio",
    "check_scan_dimensions",
    "last_blackref_dir",
    "last_whiteref_dir",
    "last_scan_dir",
    "last_scan_file",
    "last_image_dir",
    "scale_r",
    "scale_g",
    "scale_b",
    "annotation_color",
    "redis_host",
    "redis_port",
    "redis_pw",
    "redis_in",
    "redis_out",
    "redis_connect",
    "marker_size",
    "marker_color",
    "min_obj_size",
]


class SessionManager(AbstractSessionManager):
    """
    For managing the session parameters.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        super().__init__()
        self.autodetect_channels = False
        self.keep_aspectratio = False
        self.check_scan_dimensions = True
        self.last_blackref_dir = ""
        self.last_whiteref_dir = ""
        self.last_scan_dir = ""
        self.last_scan_file = ""
        self.last_image_dir = ""
        self.scale_r = 0
        self.scale_g = 0
        self.scale_b = 0
        self.annotation_color = "#ff0000"
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.redis_pw = None
        self.redis_in = "sam_in"
        self.redis_out = "sam_out"
        self.redis_connect = False
        self.marker_size = 7
        self.marker_color = "#ff0000"
        self.min_obj_size = -1

    def get_default_config_name(self):
        """
        Returns the filename (no path) of the session config file.

        :return: the name
        :rtype: str
        """
        return "envi_viewer.json"

    def get_properties(self):
        """
        Returns the list of properties of the session manager to save/load.

        :return: the list of property names
        :rtype: list
        """
        return PROPERTIES
