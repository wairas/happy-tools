from typing import Optional
from ._core import AbstractReferenceLocator


class ManualLocator(AbstractReferenceLocator):

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "rl-manual"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Reference locator where the user has to manually locate the reference file."

    def _do_locate(self, scan_file) -> Optional[str]:
        """
        Attempts to locate the reference file using the supplied scan file.

        :param scan_file: the scan file to use as basis for locating the reference
        :type scan_file: str
        :return: the suggested reference file name, None if failed to do so
        :rtype: str
        """
        return None
