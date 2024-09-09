import numpy as np

from ._core import AbstractAnnotationBasedBlackReferenceMethod


class BlackReferenceAnnotationAverage(AbstractAnnotationBasedBlackReferenceMethod):
    """
    Computes the average per band in the annotation rectangle.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self._annotation = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-annotation-avg"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Black reference method that computes the average per band in the annotation rectangle. Does not require scan and reference to have the same size."

    def _do_apply(self, scan):
        """
        Applies the black reference to the scan and returns the updated scan.

        :param scan: the scan to apply the black reference to
        :return: the updated scan
        """
        top, left, bottom, right = self._annotation
        self.logger().info("using annotation: top=%d, left=%d, bottom=%d, right=%d" % (top, left, bottom, right))

        blackref = self.reference[top:bottom, left:right, :]
        if self.reference.shape[2] != scan.shape[2]:
            raise Exception("Reference and scan have differing number of bands: %d != %d" % (self.reference.shape[2], scan.shape[2]))

        blackref_annotation = []
        for i in range(self.reference):
            blackref_annotation.append(np.average(blackref[:, :, i]))
        self.logger().info(f"blackref_annotation: {blackref_annotation}")

        result = scan.copy()
        for i in range(len(blackref_annotation)):
            if blackref_annotation[i] != 1.0:
                result[:, :, i] -= blackref_annotation[i]
        return result
