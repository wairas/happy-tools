import argparse
import numpy as np

from PIL import Image, ImageDraw

from happy.data import LABEL_WHITEREF, LABEL_BLACKREF
from ._core import AbstractOPEXAnnotationBasedNormalization, channel_to_str


class ObjectAnnotationsNormalization(AbstractOPEXAnnotationBasedNormalization):
    """
    Normalization that only uses pixels from annotations (excl white/black references)
    to calculate the min/max/range.
    """

    def __init__(self):
        super().__init__()
        self._labels = []

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
        return "Normalization that only uses pixels from annotations (white/black references are always skipped) to calculate the min/max/range."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-l", "--label", metavar="LABEL", type=str, help="The labels to restrict the calculation to rather than all (except white/black reference)", required=False, nargs="*")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._labels = ns.label

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        # generate mask
        img = Image.new("1", (data.shape[1], data.shape[0]))
        draw = ImageDraw.Draw(img)
        labels = None
        if (self._labels is not None) and (len(self._labels) > 0):
            labels = set(self._labels)
        for obj in self.annotations.objects:
            if (obj.label == LABEL_WHITEREF) or (obj.label == LABEL_BLACKREF):
                continue
            if (labels is not None) and (obj.label not in labels):
                continue
            poly = [tuple(x) for x in obj.polygon.points]
            draw.polygon(poly, fill=1)
        mask = np.array(img)
        masked_data = np.ma.masked_array(data, mask)

        # determine min/max
        min_value = np.ma.min(masked_data)
        max_value = np.ma.max(masked_data)
        data_range = max_value - min_value
        self.logger().info("channel=%s, min=%f, max=%f, range=%f" % (channel_to_str(channel), min_value, max_value, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = np.clip(data, min_value, max_value)
            data = (data - min_value) / data_range
        return data
