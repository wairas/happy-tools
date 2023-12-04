import numpy as np

from ._core import AbstractFileBasedBlackReferenceMethod


class BlackReferenceColumnAverage(AbstractFileBasedBlackReferenceMethod):
    """
    Computes the average per band per column.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self._avg = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-col-avg"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Black reference method that computes the average per band, per column. Requires the scan and reference to have the same number of columns."

    def _do_initialize(self):
        """
        Hook method for initializing the black reference method.
        """
        super()._do_initialize()
        num_columns = self.reference.shape[1]
        self._avg = []
        for col in range(num_columns):
            self._avg.append(np.mean(self.reference[:, col, :], axis=0))
        self.logger().info(f"average: {self._avg}")

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        # ensure that number of cols match
        if scan.shape[1] != self.reference.shape[1]:
            raise Exception("The number of columns in the scan differ from the black reference ones: %d != %d" % (scan.shape[1], self.reference.shape[1]))
        result = scan.copy()
        for col in range(len(self._avg)):
            result[:, col, :] -= self._avg[col]
        return result
