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
        self.logger().info("using annotation: top=%d, left=%d, bottom=%d, right=%d" % (top, left, bottom, right))

        whiteref = self.reference[top:bottom, left:right, :]
        if self.reference.shape[2] != scan.shape[2]:
            raise Exception("Reference and scan have differing number of bands: %d != %d" % (self.reference.shape[2], scan.shape[2]))

        whiteref_annotation = []
        for i in range(self.reference.shape[2]):
            whiteref_annotation.append(np.average(whiteref[:, :, i]))
        self.logger().info(f"whiteref_annotation: {whiteref_annotation}")

        result = scan.copy()
        for i in range(len(whiteref_annotation)):
            if whiteref_annotation[i] != 1.0:
                result[:, :, i] /= whiteref_annotation[i]
        return result
