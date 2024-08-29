import json
import numpy as np
import os
import spectral.io.envi as envi
import traceback

from typing import Optional, Dict, Tuple

from PIL import Image, ImageDraw
from ._metadata import MetaDataManager
from ._palette import tableau_colors
from happy.base.config import get_config_dir


BRUSH_SHAPE_ROUND = "round"
BRUSH_SHAPE_SQUARE = "square"
BRUSH_SHAPES = [
    BRUSH_SHAPE_ROUND,
    BRUSH_SHAPE_SQUARE,
]

MASK_PREFIX = "MASK_"


def generate_cursor(shape: str, size: int, path: str, width: int = None, height: int = None):
    """
    Generates an XBM image for a cursor.

    :param shape: the cursor shape
    :type shape: str
    :param size: the size of the shape (width and height)
    :type size: int
    :param path: where to store the image
    :type: str
    :param width: the width of the shape, overrides size
    :type width: int
    :param height: the height of the shape, overrides size
    :type height: int
    """
    if (width is None) or (height is None):
        width = size
        height = size
    img = Image.new("1", (width + 3, height + 3))
    draw = ImageDraw.Draw(img)
    if shape == BRUSH_SHAPE_ROUND:
        draw.ellipse((1, 1, width + 1, height + 1), width=1, outline=1)
    elif shape == BRUSH_SHAPE_SQUARE:
        draw.rectangle((1, 1, width + 1, height + 1), width=1, outline=1)
    else:
        raise Exception("Unhandled cursor shape: %s" % shape)
    img.save(path, format="xbm", hotspot=(int(width / 2) + 3, int(height / 2) + 3))


def load_label_map(path: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Loads the label map, if possible.

    :param path: the map in JSON format to load
    :type path: str
    :return: the tuple of label map and potential error message
    :rtype: tuple
    """
    if not os.path.exists(path):
        return None, "Label map does not exist: %s" % path
    try:
        with open(path, "r") as fp:
            d = json.load(fp)
        for k in d:
            try:
                int(k)
            except:
                return "Found non-integer index: %s" % k
            if not isinstance(d[k], str):
                return "Found non-string label for index: %d" % k
        return d, None
    except:
        return None, "Failed to load label map: %s\n%s" % (path, traceback.format_exc())


class PixelManager:
    """
    For managing pixel annotations.
    """

    def __init__(self, brush_shape=BRUSH_SHAPE_ROUND, brush_size=7, metadata=None, palette=None, log_method=None):
        """
        Initializes the pixel manager.

        :param brush_shape: the shape for the brush to use
        :type brush_shape: str
        :param brush_size: the size of the brush in pixels
        :type brush_size: int
        :param metadata: the meta-data manager to use
        :type metadata: MetaDataManager
        :param palette: the palette to use (list of (r,g,b) tuples), auto-generates one if None
        :type palette: list
        :param log_method: the method to send log messages to
        """
        self._image_indexed = None
        self._image_rgba = None
        self._draw_indexed = None
        self._draw_rgba = None
        self._brush_shape = None
        self._brush_size = None
        self._label = 1
        self._palette = None
        self._alpha = None
        self._cursor_path = None
        self._zoom_x = 1.0
        self._zoom_y = 1.0
        self._invert_cursor = False
        self.label_map = dict()
        self.internal_metadata = False
        self.log_method = log_method

        if metadata is None:
            self.internal_metadata = True
            metadata = MetaDataManager()
        self.metadata = metadata
        self.brush_shape = brush_shape
        self.brush_size = brush_size
        if palette is None:
            palette = tableau_colors()
        self.palette = palette
        self.alpha = 128

    def log(self, msg):
        """
        For logging messages. If no log_method set, then stdout is used.

        :param msg: the message to log
        :type msg: str
        """
        if self.log_method is None:
            print(msg)
        else:
            self.log_method(msg)

    def clear(self):
        """
        Removes the internal images.
        """
        if self._image_indexed is not None:
            width, height = self._image_indexed.size
            self._draw_indexed.rectangle((0, 0, width - 1, height - 1), fill=0)
            self._draw_rgba.rectangle((0, 0, width - 1, height - 1), fill=(0, 0, 0, 0))
        self.clear_label_map()

    def has_annotations(self):
        """
        Checks whether any annotations are present.

        :return: True if annotations are present
        :rtype: bool
        """
        result = False
        if self._image_indexed is not None:
            unique = list(np.unique(self._image_indexed))
            if 0 in unique:
                unique.remove(0)
            result = len(unique) > 0
        return result

    def reshape(self, width, height):
        """
        Re-initializes the internal image with the specified width/height.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        """
        self._image_indexed = Image.new(mode='L', size=(width, height))
        self._draw_indexed = ImageDraw.Draw(self._image_indexed)
        self._image_rgba = Image.new(mode='RGBA', size=(width, height), color=None)
        self._draw_rgba = ImageDraw.Draw(self._image_rgba)

    def _create_cursor(self):
        """
        Creates a cursor image, if necessary.
        """
        if self._brush_shape is None:
            return
        if self._brush_size is None:
            return
        if (self.zoom_x == 1.0) and (self.zoom_y == 1.0):
            width = self._brush_size
            height = self._brush_size
        else:
            width = int(self._brush_size * self.zoom_x)
            height = int(self._brush_size * self.zoom_y)
        path = os.path.join(get_config_dir(), "%s-%d-%d.xbm" % (self._brush_shape, width, height))
        if not os.path.exists(path):
            self.log("Saving cursor: %s" % path)
            if (self.zoom_x == 1.0) and (self.zoom_y == 1.0):
                generate_cursor(self._brush_shape, self._brush_size, path)
            else:
                generate_cursor(self._brush_shape, self._brush_size, path,
                                width=width, height=height)
        self._cursor_path = path

    @property
    def cursor_path(self):
        """
        Returns the cursor path.

        :return: the path, None if not yet set
        :rtype: str
        """
        return self._cursor_path

    @property
    def brush_shape(self):
        """
        Returns the brush shape in use.
        
        :return: the shape
        :rtype: str 
        """
        return self._brush_shape

    @brush_shape.setter
    def brush_shape(self, brush_shape):
        """
        Sets the brush shape to use.
        
        :param brush_shape: the shape
        :type brush_shape: str 
        """
        if brush_shape not in BRUSH_SHAPES:
            raise Exception("Unsupported brush shape: %s" % brush_shape)
        self._brush_shape = brush_shape
        self._create_cursor()

    @property
    def brush_size(self):
        """
        Returns the brush size in use.

        :return: the size
        :rtype: int
        """
        return self._brush_size

    @brush_size.setter
    def brush_size(self, brush_size):
        """
        Sets the brush size to use.

        :param brush_size: the size
        :type brush_size: int
        """
        if brush_size < 1:
            raise Exception("Unsupported brush size: %d" % brush_size)
        self._brush_size = brush_size
        self._create_cursor()

    @property
    def zoom_x(self):
        """
        Returns the zoom for x axis.

        :return: the zoom
        :rtype: float
        """
        return self._zoom_x

    @zoom_x.setter
    def zoom_x(self, zoom):
        """
        Sets the zoom for the x axis.

        :param zoom: the zoom
        :type zoom: float
        """
        self._zoom_x = zoom
        self._create_cursor()

    @property
    def zoom_y(self):
        """
        Returns the zoom for y axis.

        :return: the zoom
        :rtype: float
        """
        return self._zoom_y

    @zoom_y.setter
    def zoom_y(self, zoom):
        """
        Sets the zoom for the y axis.

        :param zoom: the zoom
        :type zoom: float
        """
        self._zoom_y = zoom
        self._create_cursor()

    @property
    def label(self):
        """
        Returns the label index in use.

        :return: the label index
        :rtype: int
        """
        return self._label

    @property
    def invert_cursor(self):
        """
        Returns whether to invert the color for the cursor.

        :return: whether to invert
        :rtype: bool
        """
        return self._invert_cursor

    @invert_cursor.setter
    def invert_cursor(self, invert):
        """
        Sets whether to invert the color for the cursor.

        :param invert: true if to invert
        :type invert: bool
        """
        self._invert_cursor = invert
        self._create_cursor()

    @label.setter
    def label(self, label):
        """
        Sets the label index to use.

        :param label: the label index
        :type label: int
        """
        if (label < 1) or (label > 255):
            raise Exception("Unsupported label index: %d" % label)
        self._label = label

    @property
    def palette(self):
        """
        Returns the palette in use.

        :return: the palette (list of (r,g,b) tuples)
        :rtype: list
        """
        return self._palette

    @palette.setter
    def palette(self, palette):
        """
        Sets the palette to use.

        :param palette: the palette (list of (r,g,b) tuples)
        :type palette: list
        """
        self._palette = palette

    @property
    def alpha(self):
        """
        Returns the alpha value in use.

        :return: the alpha (0: transparent, 255: opaque)
        :rtype: int
        """
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        """
        Sets the alpha value to use.

        :param alpha: the alpha (0: transparent, 255: opaque)
        :type alpha: int
        """
        if (alpha < 0) or (alpha > 255):
            raise Exception("Unsupported alpha value: %d" % alpha)

        if alpha != self._alpha:
            self._alpha = alpha
            if self._image_rgba is not None:
                self._image_rgba.putalpha(alpha)

                # based on: https://stackoverflow.com/a/3753428/4698227
                data = np.array(self._image_rgba)  # "data" is a height x width x 4 numpy array
                red, green, blue, alpha = data.T  # Temporarily unpack the bands for readability
                # set black back to full transparency
                black_areas = (red == 0) & (blue == 0) & (green == 0)
                data[black_areas.T] = (0, 0, 0, 0)
                # recreate PIL objects
                self._image_rgba = Image.fromarray(data)
                self._draw_rgba = ImageDraw.Draw(self._image_rgba)

    def _draw(self, points, add):
        """
        Draws the brush shape for all the supplied (center) points.

        :param points: the points to draw (list of (x,y) tuple)
        :type points: list
        :param add: whether to add or remove
        :type add: bool
        """
        if add:
            label = self.label
            r, g, b = self.palette[self.label - 1]
            rgba = (r, g, b, self.alpha)
        else:
            label = 0
            rgba = (0, 0, 0, 0)
        for x, y in points:
            if self.brush_shape == BRUSH_SHAPE_ROUND:
                x0 = int(x - self.brush_size / 2)
                x1 = int(x + self.brush_size / 2)
                y0 = int(y - self.brush_size / 2)
                y1 = int(y + self.brush_size / 2)
                xy = (x0, y0, x1, y1)
                self._draw_indexed.ellipse(xy, fill=label, outline=label)
                self._draw_rgba.ellipse(xy, fill=rgba, outline=rgba)
            elif self.brush_shape == BRUSH_SHAPE_SQUARE:
                x0 = int(x - self.brush_size / 2)
                x1 = int(x + self.brush_size / 2)
                y0 = int(y - self.brush_size / 2)
                y1 = int(y + self.brush_size / 2)
                xy = (x0, y0, x1, y1)
                self._draw_indexed.rectangle(xy, fill=label, outline=label)
                self._draw_rgba.rectangle(xy, fill=rgba, outline=rgba)
            else:
                raise Exception("Unsupported brush shape: %s" % self.brush_shape)

    def add(self, points):
        """
        Applies the brush at the specified points to add annotations.

        :param points: the points to draw (list of (x,y) tuple)
        :type points: list
        """
        self._draw(points, True)

    def remove(self, points):
        """
        Applies the brush at the specified points to remove annotations.

        :param points: the points to draw (list of (x,y) tuple)
        :type points: list
        """
        self._draw(points, False)

    def add_polygons(self, contours_list):
        """
        Draws the polygons using the selected label.

        :param contours_list: the list of polygons to draw (list of list of x/y tuples)
        :type contours_list: list
        """
        label = self.label
        r, g, b = self.palette[self.label - 1]
        rgba = (r, g, b, self.alpha)
        w, h = self._image_indexed.size
        for contours in contours_list:
            xy = [(xyn[0]*w, xyn[1]*h) for xyn in contours]
            self._draw_indexed.polygon(xy, fill=label, outline=label)
            self._draw_rgba.polygon(xy, fill=rgba, outline=rgba)

    def to_overlay(self, width, height):
        """
        Generates an overlay image.

        :param width: the width for the overlay
        :type width: int
        :param height: the height for the overlay
        :type height: int
        :return: the Image or None if no image available
        :rtype: Image.Image
        """
        if self._image_rgba is None:
            return None
        w, h = self._image_rgba.size
        if (w != width) or (h != height):
            return self._image_rgba.resize((width, height), Image.LANCZOS)
        else:
            return self._image_rgba

    def unique_values(self):
        """
        Returns the unique values in the indexed image.

        :return: the list of unique values
        :rtype: list
        """
        if self._image_indexed is None:
            return list()
        else:
            return list(np.unique(np.array(self._image_indexed)))

    def save_png(self, path):
        """
        Saves the internal image as PNG.

        :param path: the path to save the image to
        :type path: str
        :return: if successfully saved
        :rtype: bool
        """
        if self._image_indexed is None:
            return False
        try:
            self._image_indexed.save(path)
            return True
        except:
            self.log("Failed to save PNG to: %s\n%s" % (path, traceback.format_exc()))
            return False

    def save_envi(self, path):
        """
        Saves the annotation as ENVI file.

        :param path: the .hdr file to save to
        :type path: str
        :return: if successfully saved
        :rtype: bool
        """
        if self._image_indexed is None:
            return False
        try:
            metadata = {}
            if len(self.metadata) > 0:
                metadata = self.metadata.to_dict()
            envi.save_image(path, np.array(self._image_indexed), dtype=None, force=True, interleave='BSQ', metadata=metadata)
            return True
        except:
            self.log("Failed to save ENVI to: %s\n%s" % (path, traceback.format_exc()))
            return False

    def load_envi(self, path):
        """
        Loads the annotations from the specified ENVI file.
        
        :param path: the ENVI file to load
        :type path: str
        """
        img = envi.open(path)
        data = img.load()
        palette = [0, 0, 0] + [item for sublist in self.palette for item in sublist]
        self._image_indexed = Image.fromarray(data.squeeze().astype(np.uint8), mode="L")
        self._image_indexed.putpalette(palette)
        self._draw_indexed = ImageDraw.Draw(self._image_indexed)
        rgba = self._image_indexed.copy().convert(mode="RGB")
        rgba.putalpha(self.alpha)
        data = np.array(rgba)  # "data" is a height x width x 4 numpy array
        red, green, blue, alpha = data.T  # Temporarily unpack the bands for readability
        # set black back to full transparency
        black_areas = (red == 0) & (blue == 0) & (green == 0)
        data[black_areas.T] = (0, 0, 0, 0)
        self._image_rgba = Image.fromarray(data)
        self._draw_rgba = ImageDraw.Draw(self._image_rgba)

    def clear_label_map(self):
        """
        Empties the label map.
        """
        self.label_map.clear()

    def update_label_map(self, index: int, label: str):
        """
        Sets the label associated with the index.

        :param index: the index to set the label string for
        :type index: int
        :param label: the label to use for the index
        :type label: int
        """
        self.label_map[index] = label

    def save_label_map(self, path: str) -> bool:
        """
        Saves the current label map in JSON format to the specified file.

        :param path: the path to save the map to
        :type path: str
        :return: whether saved successfully
        :rtype: bool
        """
        try:
            with open(path, "w") as fp:
                json.dump(self.label_map, fp, indent=2)
            return True
        except:
            return False

    def load_label_map(self, path: str) -> Optional[str]:
        """
        Loads the label map, if possible.

        :param path: the map in JSON format to load
        :type path: str
        :return: None if successfully loaded, otherwise error message
        :rtype: str
        """
        d, msg = load_label_map(path)
        if msg is None:
            self.label_map = d
        return msg

    def to_dict(self):
        """
        Returns its state as a dictionary.
        
        :return: the state
        :rtype: dict 
        """
        result = dict()
        if self._image_indexed is not None:
            result["indexed"] = self._image_indexed.copy()
            result["rgba"] = self._image_rgba.copy()
        return result

    def from_dict(self, d):
        """
        Initializes itself from the state dictionary.
        
        :param d: the state to restore from
        :type d: dict 
        """
        self._image_indexed = None
        self._draw_indexed = None
        self._image_rgba = None
        self._draw_rgba = None
        if ("indexed" in d) and ("rgba" in d):
            self._image_indexed = d["indexed"].copy()
            self._draw_indexed = ImageDraw.Draw(self._image_indexed)
            self._image_rgba = d["rgba"].copy()
            self._draw_rgba = ImageDraw.Draw(self._image_rgba)
