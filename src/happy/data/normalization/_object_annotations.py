import numpy as np

from PIL import Image, ImageDraw

from happy.data import LABEL_WHITEREF, LABEL_BLACKREF
from ._core import AbstractOPEXAnnotationBasedNormalization


class ObjectAnnotationsNormalization(AbstractOPEXAnnotationBasedNormalization):
    """
    Normalization that only uses pixels from annotations (excl white/black references)
    to calculate the min/max/range.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "norm-object-annotations"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Normalization that only uses pixels from annotations (excl white/black references) to calculate the min/max/range."

    def _do_normalize(self, data):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :return: the normalized data, None if failed to do so
        """
        # generate mask
        img = Image.new("1", (data.shape[1], data.shape[0]))
        draw = ImageDraw.Draw(img)
        for obj in self.annotations.objects:
            if (obj.label == LABEL_WHITEREF) or (obj.label == LABEL_BLACKREF):
                continue
            poly = [tuple(x) for x in obj.polygon.points]
            draw.polygon(poly, fill=1)
        mask = np.array(img)
        masked_data = np.ma.masked_array(data, mask)

        # determine min/max
        min_value = np.ma.min(masked_data)
        max_value = np.ma.max(masked_data)
        data_range = max_value - min_value
        self.logger().info("min=%f, max=%f, range=%f" % (min_value, max_value, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = np.clip(data, min_value, max_value)
            data = (data - min_value) / data_range
        return data
