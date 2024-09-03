import numpy as np

from ._core import AbstractNormalization, channel_to_str


class SimpleNormalization(AbstractNormalization):
    """
    Simple normalization that just determines min/max of the whole image
    and then uses that to normalize the data.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "norm-simple"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Simple normalization that just determines min/max of the whole image and then uses that to normalize the data."

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        min_value = np.min(data)
        max_value = np.max(data)
        data_range = max_value - min_value
        self.logger().info("channel=%s, min=%f, max=%f, range=%f" % (channel_to_str(channel), min_value, max_value, data_range))

        if data_range == 0:  # Handle division by zero
            data = np.zeros_like(data)
        else:
            data = (data - min_value) / data_range
        return data
