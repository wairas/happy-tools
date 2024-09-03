import argparse
import numpy as np

from ._core import AbstractNormalization, channel_to_str


class FixedNormalization(AbstractNormalization):
    """
    Uses the user-supplied min/max values to normalize the data. Values below or above get clipped.
    """

    def __init__(self):
        super().__init__()
        self._min = None
        self._max = None

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
        parser.add_argument("-m", "--min", metavar="NUM", type=float, help="The minimum value to use", required=False, default=0.0)
        parser.add_argument("-M", "--max", metavar="NUM", type=float, help="The maximum value to use", required=False, default=10000.0)
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

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        data_range = self._max - self._min
        self.logger().info("channel=%s, min=%f, max=%f, range=%f" % (channel_to_str(channel), self._min, self._max, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = np.clip(data, self._min, self._max)
            data = (data - self._min) / data_range
        return data
