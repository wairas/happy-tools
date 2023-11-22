import numpy as np

from ._core import AbstractAnnotationBasedWhiteReferenceMethod


class WhiteReferenceAnnotationAverage(AbstractAnnotationBasedWhiteReferenceMethod):
    """
    Computes the average per band in the annotation rectangle.
    """

    def __init__(self):
        """
        Basic initialization of the white reference method.
        """
        super().__init__()
        self._annotation = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "wr-annotation-avg"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "White reference method that computes the average per band in the annotation rectangle. Does not require scan and reference to have the same size."

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        top, left, bottom, right = self._annotation
        whiteref = scan[top:bottom, left:right, :]
        num_bands = scan.shape[2]
        whiteref_annotation = []
        for i in range(num_bands):
            whiteref_annotation.append(np.average(whiteref[:, :, i]))
        result = scan.copy()
        for i in range(len(whiteref_annotation)):
            if whiteref_annotation[i] != 1.0:
                result[:, :, i] /= whiteref_annotation[i]
        return result
