from ._core import AbstractFileBasedWhiteReferenceMethod


class SameSizeWhiteReference(AbstractFileBasedWhiteReferenceMethod):
    """
    Simply divides the scan by the white reference.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "wr-same-size"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Simply divides the scan by the white reference. Requires scan and reference to have the same size."

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        if self.reference.shape == scan.shape:
            return scan / self.reference
        else:
            raise Exception("White reference dimensions differ from scan: %s != %s" % (str(self.reference.shape), str(scan.shape)))
