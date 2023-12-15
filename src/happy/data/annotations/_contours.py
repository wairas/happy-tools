import copy
import json
import sys
import traceback
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

    meta: dict = None
    """ optional meta-data. """

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
        result = Contour(points_a, label=self.label, normalized=False)
        if self.meta is not None:
            result.meta = copy.copy(self.meta)
        return result

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

    def has_same_points(self, other):
        """
        Compares its own coordinates with the ones from the other contour.

        :param other: the other contour to compare with
        :type other: Contour
        :return: True if the same points
        """
        result = len(self.points) == len(other.points)

        if result:
            for i in range(len(self.points)):
                self_x, self_y = self.points[i]
                other_x, other_y = other.points[i]
                if (self_x != other_x) or (self_y != other_y):
                    result = False
                    break

        return result


class ContoursManager:
    """
    For managing all the contours.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.contours = list()
        self.metadata = dict()

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
        if not self.has_contours() and not self.has_metadata():
            return None
        start_time = datetime.now()
        objs = []
        for contours in self.to_absolute(width, height):
            for contour in contours:
                bb = contour.bbox()
                bbox = BBox(left=bb.left, top=bb.top, right=bb.right, bottom=bb.bottom)
                poly = Polygon(points=contour.points)
                label = "object" if (contour.label == "") else contour.label
                pred = ObjectPrediction(label=label, bbox=bbox, polygon=poly)
                if contour.meta is not None:
                    meta = dict()
                    for k in contour.meta:
                        o = contour.meta[k]
                        if isinstance(o, list) or isinstance(o, dict):
                            o = json.dumps(o)
                        else:
                            o = str(o)
                        meta[k] = str(o)
                    pred.meta = meta
                objs.append(pred)
        result = ObjectPredictions(id=str(start_time), timestamp=str(start_time), objects=objs)
        if len(self.metadata) > 0:
            result.meta = copy.copy(self.metadata)
        return result

    def from_opex(self, predictions, width, height):
        """
        Turns the OPEX annotations into contours.

        :param predictions: the ObjectPredictions annotations to load
        :type predictions: ObjectPredictions
        :param width: the width of the image, used for normalizing the coordinates
        :type width: int
        :param height: the height of the image, used for normalizing the coordinates
        :type height: int
        :return: whether successfully imported
        :rtype: bool
        """
        self.clear()
        if isinstance(predictions.meta, dict):
            self.metadata.update(predictions.meta)
        contours = list()
        for obj in predictions.objects:
            points = []
            for x, y in obj.polygon.points:
                points.append((x / width, y / height))
            meta = None
            if isinstance(obj.meta, dict):
                meta = obj.meta.copy()
            contour = Contour(points=points, label=obj.label, normalized=True, meta=meta)
            contours.append(contour)
        self.add(contours)

    def has_contours(self):
        """
        Checks whether any contours are stored.

        :return: True if at least one contour present
        :rtype: bool
        """
        return len(self.contours) > 0

    def clear(self):
        """
        Clears the contours and meta-data.

        :return: True if anything was cleared
        :rtype: bool
        """
        self.clear_metadata()
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

    def remove(self, contours):
        """
        Removes all the contours.

        :param contours: the list of contours to remove
        :type contours: list
        """
        # determine contour objects to remove based on coordinates
        remove_contours = []
        for other_contour in contours:
            for self_contours in self.contours:
                for self_contour in self_contours:
                    if self_contour.has_same_points(other_contour):
                        remove_contours.append(self_contour)
        # remove contours
        for remove_contour in remove_contours:
            for self_contours in self.contours:
                if remove_contour in self_contours:
                    self_contours.remove(remove_contour)

    def has_metadata(self):
        """
        Checks whether any meta-data is present.

        :return: True if meta-data present
        :rtype: bool
        """
        return len(self.metadata) > 0

    def clear_metadata(self):
        """
        Clears the metadata.
        """
        self.metadata = dict()

    def set_metadata(self, k, v):
        """
        Sets the specified meta-data value.

        :param k: the key
        :type k: str
        :param v: the associated value
        :type v: str
        """
        self.metadata[k] = v

    def remove_metadata(self, k):
        """
        Removes the specified key from the meta-data.

        :param k: the key to remove
        :type k: str
        :return: None if successfully removed, otherwise error message
        :rtype: str
        """
        if k in self.metadata:
            self.metadata.pop(k)
        else:
            return "No meta-data value stored under '%s'!" % k

    def has_label(self, label):
        """
        Checks whether the label is present.

        :param label: the label to check
        :type label: str
        :return: True if at least one present
        :rtype: bool
        """
        result = False

        for contours in self.contours:
            for contour in contours:
                if contour.has_label() and (contour.label == label):
                    result = True
                    break

        return result

    def get_contours(self, label):
        """
        Returns all the contours that have the specified label.

        :param label: the label the contours must have
        :type label: str
        :return: the list of contours with the label present, can be empty
        :rtype: list
        """
        result = []

        for contours in self.contours:
            for contour in contours:
                if contour.has_label() and (contour.label == label):
                    result.append(contour)

        return result
