import argparse
import numpy as np

from ._core import AbstractNormalization, channel_to_str, CHANNEL_RED, CHANNEL_GREEN, CHANNEL_BLUE


class FixedNormalization(AbstractNormalization):
    """
    Uses the user-supplied min/max values to normalize the data. Values below or above get clipped.
    """

    def __init__(self):
        super().__init__()
        self._min = None
        self._max = None
        self._red_min = None
        self._red_max = None
        self._green_min = None
        self._green_max = None
        self._blue_min = None
        self._blue_max = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "norm-fixed"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Uses the user-supplied min/max values to normalize the data. Values below or above get clipped."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-m", "--min", metavar="NUM", type=float, help="The minimum value to use, default for all channels", required=False, default=0.0)
        parser.add_argument("-M", "--max", metavar="NUM", type=float, help="The maximum value to use, default for all channels", required=False, default=10000.0)
        parser.add_argument("-r", "--red_min", metavar="NUM", type=float, help="The minimum value to use for the red channel", required=False, default=None)
        parser.add_argument("-R", "--red_max", metavar="NUM", type=float, help="The maximum value to use for the red channel", required=False, default=None)
        parser.add_argument("-g", "--green_min", metavar="NUM", type=float, help="The minimum value to use for the green channel", required=False, default=None)
        parser.add_argument("-G", "--green_max", metavar="NUM", type=float, help="The maximum value to use for the green channel", required=False, default=None)
        parser.add_argument("-b", "--blue_min", metavar="NUM", type=float, help="The minimum value to use for the blue channel", required=False, default=None)
        parser.add_argument("-B", "--blue_max", metavar="NUM", type=float, help="The maximum value to use for the blue channel", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._min = ns.min
        self._max = ns.max
        self._red_min = ns.red_min
        self._red_max = ns.red_max
        self._green_min = ns.green_min
        self._green_max = ns.green_max
        self._blue_min = ns.blue_min
        self._blue_max = ns.blue_max

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        # determine min/max
        _min = self._min
        _max = self._max
        if channel == CHANNEL_RED:
            if self._red_min is not None:
                _min = self._red_min
            if self._red_max is not None:
                _max = self._red_max
        elif channel == CHANNEL_GREEN:
            if self._green_min is not None:
                _min = self._green_min
            if self._green_max is not None:
                _max = self._green_max
        elif channel == CHANNEL_BLUE:
            if self._blue_min is not None:
                _min = self._blue_min
            if self._blue_max is not None:
                _max = self._blue_max

        data_range = _max - _min
        self.logger().info("channel=%s, min=%f, max=%f, range=%f" % (channel_to_str(channel), _min, _max, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = np.clip(data, _min, _max)
            data = (data - _min) / data_range
        return data
