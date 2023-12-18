import json
from PIL import Image, ImageDraw


class MarkersManager:
    """
    For managing marker points.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.points = []

    def has_points(self):
        """
        Returns whether there are any points currently present.

        :return: True if present
        :rtype: bool
        """
        return len(self.points) > 0

    def clear(self):
        """
        Clears all points.
        """
        self.points = []

    def add(self, point):
        """
        Adds the point.

        :param point: the point to add (normalized x/y tuple)
        :type point: tuple
        """
        self.points.append(point)

    def to_overlay(self, width, height, marker_size, marker_color):
        """
        Generates a new overlay image for marker points and returns it.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :param marker_size: the size of the markers
        :type marker_size: int
        :param marker_color: the color to use for the markers
        :type marker_color: str
        :return: the generated overlay
        """
        image = Image.new("RGBA", (width, height), color=None)
        draw = ImageDraw.Draw(image)
        for point in self.points:
            point_a = (point[0]*width, point[1]*height)
            bbox = [point_a[0] - marker_size // 2, point_a[1] - marker_size // 2, point_a[0] + marker_size // 2, point_a[1] + marker_size // 2]
            draw.ellipse(bbox, outline=marker_color)
        return image

    def to_absolute(self, width, height):
        """
        Returns the absolute points.

        :param width: the width of the underlying image
        :type width: int
        :param height: the height of the underlying image
        :type height: int
        :return: the absolute marker points as list of x/y tuples
        :rtype: list
        """
        return [(int(x * width), int(y * height)) for x, y in self.points]

    def has_polygon(self):
        """
        Checks whether a polygon can be created from the current points.

        :return: True if polygon possible
        :rtype: bool
        """
        return len(self.points) >= 3

    def to_spectra(self, scan):
        """
        Turns the markers into a dictionary of the coordinate strings associated
        with the numpy array of the spectral data.

        :param scan: the underlying data
        :type scan: numpy.array
        :return: the dictionary of spectra
        :rtype: dict
        """
        result = dict()

        if self.has_points():
            h, w, _ = scan.shape
            for x, y in self.points:
                x = int(x * w)
                y = int(y * h)
                label = "x=%d, y=%d" % (x, y)
                spec = scan[y, x]
                result[label] = spec

        return result

    def to_json(self):
        """
        Returns the current state as JSON string.

        :return: the markers as JSON string
        :rtype: str
        """
        return json.dumps(self.points)

    def from_json(self, s):
        """
        Restores its state from the JSON string.

        :param s: the JSON string to restore the state from
        :type s: str
        :return: whether successfully restored
        :rtype: bool
        """
        points = json.loads(s)
        if not isinstance(points, list):
            return False
        for point in points:
            if not (isinstance(point, list) or isinstance(point, tuple)):
                return False
            if len(point) != 2:
                return False

        self.clear()
        for point in points:
            self.points.append(tuple(point))

        return True
