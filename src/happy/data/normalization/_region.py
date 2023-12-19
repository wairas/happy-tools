import argparse
import numpy as np

from ._core import AbstractNormalization


class RegionNormalization(AbstractNormalization):
    """
    Uses the user-supplied min/max values to normalize the data. Values below or above get clipped.
    """

    def __init__(self):
        super().__init__()
        self._x0 = None
        self._y0 = None
        self._x1 = None
        self._y1 = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "norm-region"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Uses the min/max values determined from the specified region to normalize the data. Values below or above get clipped."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("--x0", metavar="COORD", type=int, help="The 0-based left coordinate of the region", required=False, default=0)
        parser.add_argument("--y0", metavar="COORD", type=int, help="The 0-based top coordinate of the region", required=False, default=0)
        parser.add_argument("--x1", metavar="COORD", type=int, help="The 0-based right coordinate of the region, use -1 for the edge of the image", required=False, default=-1)
        parser.add_argument("--y1", metavar="COORD", type=int, help="The 0-based bottom coordinate of the region, use -1 for the edge of the image", required=False, default=-1)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._x0 = ns.x0
        self._y0 = ns.y0
        self._x1 = ns.x1
        self._y1 = ns.y1

    def _do_normalize(self, data):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :return: the normalized data, None if failed to do so
        """
        x0 = self._x0
        y0 = self._y0
        x1 = (data.shape[1] - 1) if (self._x1 == -1) else self._x1
        y1 = (data.shape[0] - 1) if (self._y1 == -1) else self._y1
        region = data[y0:y1, x0:x1]
        min_value = np.min(region)
        max_value = np.max(region)
        data_range = max_value - min_value
        self.logger().info("min=%f, max=%f, range=%f" % (min_value, max_value, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = np.clip(data, min_value, max_value)
            data = (data - min_value) / data_range
        return data
