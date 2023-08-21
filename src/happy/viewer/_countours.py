from datetime import datetime
from operator import itemgetter

from PIL import Image, ImageDraw
from opex import BBox, Polygon, ObjectPrediction, ObjectPredictions


class ContoursManager:
    """
    For managing all the contours.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.contours = list()

    def calc_absolute_contours(self, width, height):
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
            contours_a = []
            for contour in contours:
                contour_a = []
                for coord in contour:
                    contour_a.append((int(coord[0]*width), int(coord[1]*height)))
                contours_a.append(contour_a)
            result.append(contours_a)
        return result

    def calc_contours_overlay(self, width, height, outline_color):
        """
        Generates a new overlay image for contours and returns it.

        :param width: the width to use
        :type width: int
        :param height: the height to use
        :type height: int
        :return: the generated overlay
        """
        image = Image.new("RGBA", (width, height), color=None)
        draw = ImageDraw.Draw(image)
        for contours in self.calc_absolute_contours(width, height):
            for contour in contours:
                draw.polygon(contour, outline=outline_color)
        return image

    def contours_to_opex(self, width, height):
        """
        Turns the contours into OPEX format and returns it.

        :param width: the width of the image to use
        :type width: int
        :param height: the height of the image to use
        :type height: int
        :return: the generated OPEX data structure, None if no contours available
        :rtype: ObjectPredictions
        """
        if len(self.contours) == 0:
            return None
        start_time = datetime.now()
        objs = []
        for contours in self.calc_absolute_contours(width, height):
            for contour in contours:
                # https://stackoverflow.com/a/13145419/4698227
                min_xy = min(contour, key=itemgetter(0))[0], min(contour, key=itemgetter(1))[1]
                max_xy = max(contour, key=itemgetter(0))[0], max(contour, key=itemgetter(1))[1]
                bbox = BBox(left=min_xy[0], top=min_xy[1], right=max_xy[0], bottom=max_xy[1])
                poly = Polygon(points=contour)
                pred = ObjectPrediction(label="object", bbox=bbox, polygon=poly)
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
        Adds the contours.

        :param contours: the contours to add
        :type contours: list
        """
        self.contours.append(contours)

    def remove_last(self):
        """
        Removes the last contour.

        :return: True if a contour was removed
        :rtype: bool
        """
        if len(self.contours) > 0:
            self.contours.pop()
            return True
        else:
            return False