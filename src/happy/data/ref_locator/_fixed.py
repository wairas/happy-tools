import argparse
from typing import Optional

from ._core import AbstractReferenceLocator


class FixedLocator(AbstractReferenceLocator):

    def __init__(self):
        """
        Initializes the locator.
        """
        super().__init__()
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

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()
        if result is None:
            if (self._reference_file is None) or (len(self._reference_file) == 0):
                result = "No reference file specified!"
        return result

    def _do_locate(self):
        """
        Attempts to locate the reference data.

        :return: the suggested reference data, None if failed to do so
        """
        return self._reference_file
