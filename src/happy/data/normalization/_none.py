from ._core import AbstractNormalization


class NoneNormalization(AbstractNormalization):
    """
    Performs no normalization.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "norm-none"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Performs no normalization."

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        return data
