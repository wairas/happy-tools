from happy.gui.session import AbstractSessionManager
from happy.data.annotations import BRUSH_SHAPE_ROUND
from ._annotations import ANNOTATION_MODE_POLYGONS


PROPERTIES = [
    "autodetect_channels",
    "keep_aspectratio",
    "check_scan_dimensions",
    "export_to_scan_dir",
    "last_blackref_dir",
    "last_whiteref_dir",
    "last_scan_dir",
    "last_scan_file",
    "last_image_dir",
    "last_session_dir",
    "scale_r",
    "scale_g",
    "scale_b",
    "annotation_color",
    "predefined_labels",
    "redis_host",
    "redis_port",
    "redis_pw",
    "redis_in",
    "redis_out",
    "redis_connect",
    "marker_size",
    "marker_color",
    "min_obj_size",
    "black_ref_locator",
    "black_ref_method",
    "white_ref_locator",
    "white_ref_method",
    "preprocessing",
    "export_overlay_annotations",
    "export_keep_aspectratio",
    "zoom",
    "normalization",
    "annotation_mode",
    "brush_shape",
    "brush_size",
    "invert_cursor",
    "alpha",
    "show_polygon_annotations",
    "show_pixel_annotations",
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
        self.autodetect_channels = False
        self.keep_aspectratio = False
        self.check_scan_dimensions = True
        self.last_blackref_dir = ""
        self.last_whiteref_dir = ""
        self.last_scan_dir = ""
        self.last_scan_file = ""
        self.last_image_dir = ""
        self.last_session_dir = "."
        self.scale_r = 0
        self.scale_g = 0
        self.scale_b = 0
        self.annotation_color = "#ff0000"
        self.predefined_labels = ""
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.redis_pw = None
        self.redis_in = "sam_in"
        self.redis_out = "sam_out"
        self.redis_connect = False
        self.marker_size = 7
        self.marker_color = "#ff0000"
        self.min_obj_size = -1
        self.black_ref_locator = "rl-manual"
        self.black_ref_method = "br-same-size"
        self.white_ref_locator = "rl-manual"
        self.white_ref_method = "wr-same-size"
        self.preprocessing = ""
        self.export_to_scan_dir = False
        self.export_overlay_annotations = False
        self.export_keep_aspectratio = True
        self.export_enforce_mask_prefix = True
        self.zoom = -1
        self.normalization = ""
        self.annotation_mode = ANNOTATION_MODE_POLYGONS
        self.brush_shape = BRUSH_SHAPE_ROUND
        self.brush_size = 7
        self.invert_cursor = False
        self.alpha = 128
        self.show_polygon_annotations = True
        self.show_pixel_annotations = True

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
