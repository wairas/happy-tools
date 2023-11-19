from ._core import AbstractBlackReferenceMethod


class NoBlackReference(AbstractBlackReferenceMethod):
    """
    Applies no black reference.
    """

    def __init__(self):
        super().__init__()
        self._reference = False  # to pass the check

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-none"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Black reference method to be used when not applying a black reference."

    def _do_apply(self, scan):
        """
        Applies the black reference to the scan and returns the updated scan.

        :param scan: the scan to apply the black reference to
        :return: the updated scan
        """
        return scan
