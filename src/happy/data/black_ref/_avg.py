import numpy as np

from ._core import AbstractFileBasedBlackReferenceMethod


class BlackReferenceAverage(AbstractFileBasedBlackReferenceMethod):
    """
    Computes the average per band.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self._black_reference_avg = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-avg"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Black reference method that computes the average per band. Does not require scan and reference to have the same size."

    def _do_initialize(self):
        """
        Hook method for initializing the black reference method.
        """
        super()._do_initialize()
        self._black_reference_avg = []
        num_bands = self.reference.shape[2]
        self._black_reference_avg = []
        for i in range(num_bands):
            self._black_reference_avg.append(np.average(self.reference[:, :, i]))

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        black_ref = np.empty_like(scan)
        for i in range(black_ref.shape[2]):
            black_ref[:, :, i] = self._black_reference_avg[i]
        return scan - black_ref
