from dataclasses import dataclass
from datetime import datetime
from operator import itemgetter

from PIL import Image, ImageDraw
from opex import BBox, Polygon, ObjectPrediction, ObjectPredictions
from shapely.geometry import Point as SPoint
from shapely.geometry.polygon import Polygon as SPolygon


@dataclass
class BBoxNormalized:
    """
    Encapsulates a bounding box.
    """
    left: float
    top: float
    right: float
    bottom: float


@dataclass
class BBoxAbsolute:
    """
    Encapsulates a bounding box.
    """
    left: int
    top: int
    right: int
    bottom: int


@dataclass
class Contour:

    points: list
    """ the list of x/y tuples that make up the contour. """

    label: str = ""
    """ the label for the contour. """

    normalized: bool = True
    """ whether normalized or absolute coordinates. """

    def has_label(self):
        """
        Checks whether an actual label is present.

        :return: True if present
        :rtype: bool
        """
        return (self.label is not None) and (len(self.label) > 0)

    def to_absolute(self, width, height):
        """
        Calculates the absolute contour from the normalized one.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the absolute contour
        :rtype: Contour
        """
        points_a = []
        for coord in self.points:
            points_a.append((int(coord[0] * width), int(coord[1] * height)))
        return Contour(points_a, label=self.label, normalized=False)

    def bbox(self):
        """
        Determines the bounding box of the contour.

        :return: the bounding box
        :rtype: BBoxNormalized or BBoxAbsolute
        """
        # https://stackoverflow.com/a/13145419/4698227
        min_xy = min(self.points, key=itemgetter(0))[0], min(self.points, key=itemgetter(1))[1]
        max_xy = max(self.points, key=itemgetter(0))[0], max(self.points, key=itemgetter(1))[1]
        if self.normalized:
            return BBoxNormalized(left=float(min_xy[0]), top=float(min_xy[1]), right=float(max_xy[0]), bottom=float(max_xy[1]))
        else:
            return BBoxAbsolute(left=int(min_xy[0]), top=int(min_xy[1]), right=int(max_xy[0]), bottom=int(max_xy[1]))


class ContoursManager:
    """
    For managing all the contours.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.contours = list()

    def to_absolute(self, width, height):
        """
        Calculates the absolute contours from the normalized ones.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the absolute contours
        :rtype: list
        """
        result = []
        for contours in self.contours:
            result.append([x.to_absolute(width, height) for x in contours])
        return result

    def to_overlay(self, width, height, outline_color):
        """
        Generates a new overlay image for contours and returns it.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :param outline_color: the color for the outline
        :type outline_color: str
        :return: the generated overlay
        """
        image = Image.new("RGBA", (width, height), color=None)
        draw = ImageDraw.Draw(image)
        for contours in self.to_absolute(width, height):
            for contour in contours:
                draw.polygon(contour.points, outline=outline_color)
                if contour.has_label():
                    bbox = contour.bbox()
                    w, h = draw.textsize(contour.label)
                    draw.text(
                        (
                            bbox.left + (bbox.right - bbox.left - w) / 2,
                            bbox.top + (bbox.bottom - bbox.top - h) / 2
                        ),
                        contour.label,
                        fill=outline_color)
        return image

    def to_opex(self, width, height):
        """
        Turns the contours into OPEX format and returns it.

        :param width: the width of the image to use
        :type width: int
        :param height: the height of the image to use
        :type height: int
        :return: the generated OPEX data structure, None if no contours available
        :rtype: ObjectPredictions
        """
        if not self.has_contours():
            return None
        start_time = datetime.now()
        objs = []
        for contours in self.to_absolute(width, height):
            for contour in contours:
                bb = contour.bbox()
                bbox = BBox(left=bb.left, top=bb.top, right=bb.right, bottom=bb.bottom)
                poly = Polygon(points=contour.points)
                label = "object" if (contour.label is "") else contour.label
                pred = ObjectPrediction(label=label, bbox=bbox, polygon=poly)
                objs.append(pred)
        result = ObjectPredictions(id=str(start_time), timestamp=str(start_time), objects=objs)
        return result

    def has_contours(self):
        """
        Checks whether any contours are stored.

        :return: True if at least one contour present
        :rtype: bool
        """
        return len(self.contours) > 0

    def clear(self):
        """
        Clears the contours.

        :return: True if anything was cleared
        :rtype: bool
        """
        if len(self.contours) > 0:
            self.contours = []
            return True
        else:
            return False

    def add(self, contours):
        """
        Adds a set of contours.

        :param contours: the set of contours to add
        :type contours: list
        """
        self.contours.append(contours)

    def remove_last(self):
        """
        Removes the last set of contours.

        :return: True if a set was removed
        :rtype: bool
        """
        if len(self.contours) > 0:
            self.contours.pop()
            return True
        else:
            return False

    def contains(self, x, y):
        """
        Returns all the contours that contain the specified (normalized) coordinates.

        :param x: the normalized x to look for
        :type x: float
        :param y: the normalized y to look for
        :type y: float
        :return: the list of contours that contain the point
        :rtype: list
        """
        result = []
        point = SPoint(x, y)
        for contours in self.contours:
            for contour in contours:
                polygon = SPolygon(contour.points)
                if polygon.contains(point):
                    result.append(contour)
        return result
