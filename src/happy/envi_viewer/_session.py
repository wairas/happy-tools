import json
import os


PROPERTIES = [
    "autodetect_channels",
    "keep_aspectratio",
    "last_blackref_dir",
    "last_whiteref_dir",
    "last_scan_dir",
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


class SessionManager:
    """
    For managing the session parameters.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.autodetect_channels = False
        self.keep_aspectratio = False
        self.last_blackref_dir = "."
        self.last_whiteref_dir = "."
        self.last_scan_dir = "."
        self.last_image_dir = "."
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

    def get_default_config_path(self):
        """
        Returns the default config file location.

        :return: the default config file
        :rtype: str
        """
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".config", "happy")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return os.path.join(config_dir, "envi_viewer.json")

    def save(self, path=None):
        """
        Saves the session (as json).

        :param path: the file to save to, uses a default location when None
        :type path: str
        """
        data = dict()
        for p in PROPERTIES:
            data[p] = getattr(self, p)

        if path is None:
            path = self.get_default_config_path()

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

        with open(path, "r") as fp:
            data = json.load(fp)

        for p in PROPERTIES:
            if p in data:
                setattr(self, p, data[p])
