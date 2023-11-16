from ._core import AbstractFileBasedBlackReferenceMethod


class SameSizeBlackReference(AbstractFileBasedBlackReferenceMethod):
    """
    Simply subtracts the black reference from the scan.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-same-size"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Simply subtracts the black reference from the scan. Requires scan and reference to have the same size."

    def _do_apply(self, scan):
        """
        Applies the black reference to the scan and returns the updated scan.

        :param scan: the scan to apply the black reference to
        :return: the updated scan
        """
        if self.reference.shape == scan.shape:
            return scan - self.reference
        else:
            raise Exception("Black reference dimensions differ from scan: %s != %s" % (str(self.reference.shape), str(scan.shape)))
