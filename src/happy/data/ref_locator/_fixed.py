import argparse
from typing import Optional

from ._core import AbstractReferenceLocator


class FixedLocator(AbstractReferenceLocator):

    def __init__(self):
        """
        Initializes the locator.
        """
        self._reference_file = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "rl-fixed"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Reference locator that always returns the specified reference file name."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-f", "--reference_file", metavar="FILE", type=str, help="The fixed reference file to use.")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._reference_file = ns.reference_file

    def _check(self, scan_file: str) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the file.

        :param scan_file: the scan file to use for locating
        :type scan_file: str
        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._check(scan_file)
        if result is None:
            if (self._reference_file is None) or (len(self._reference_file) == 0):
                result = "No reference file specified!"
        return result

    def _do_locate(self, scan_file: str) -> Optional[str]:
        """
        Attempts to locate the reference file using the supplied scan file.

        :param scan_file: the scan file to use as basis for locating the reference
        :type scan_file: str
        :return: the suggested reference file name, None if failed to do so
        :rtype: str
        """
        return self._reference_file