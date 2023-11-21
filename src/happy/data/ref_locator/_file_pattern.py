import argparse
import os
from typing import Optional

from ._core import AbstractFileBasedReferenceLocator

PH_PATH = "{PATH}"
""" the path placeholder in the pattern. """

PH_NAME = "{NAME}"
""" the file name placeholder in the pattern (excl ext). """

PH_EXT = "{EXT}"
""" the extension placeholder in the pattern. """

PLACEHOLDERS = [
    PH_PATH,
    PH_NAME,
    PH_EXT,
]


class FilePatternLocator(AbstractFileBasedReferenceLocator):

    def __init__(self):
        """
        Initializes the locator.
        """
        super().__init__()
        self._pattern = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "rl-file-pattern"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Reference locator that uses the supplied pattern and applies that to the incoming scan file name to generate the reference file name."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-p", "--pattern", metavar="PATTERN", type=str, help="The pattern to use for generating a reference file name from the scan file; available placeholders: " + ", ".join(PLACEHOLDERS), required=False, default=PH_PATH + "/" + PH_NAME + PH_EXT)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._pattern = ns.pattern

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the file.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()
        if result is None:
            if (self._pattern is None) or (len(self._pattern) == 0):
                result = "No pattern defined!"
        return result

    def _do_locate(self):
        """
        Attempts to locate the reference file using the supplied scan file.

        :return: the suggested reference file name, None if failed to do so
        """
        p = os.path.dirname(self.base_file)
        n, e = os.path.splitext(os.path.basename(self.base_file))
        result = self._pattern.replace(PH_PATH, p).replace(PH_NAME, n).replace(PH_EXT, e)
        return result
