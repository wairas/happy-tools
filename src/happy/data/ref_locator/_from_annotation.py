import argparse
from typing import Optional

from ._core import AbstractOPEXAnnotationBasedReferenceLocator
from opex import ObjectPrediction


class FromAnnotationLocator(AbstractOPEXAnnotationBasedReferenceLocator):

    def __init__(self):
        """
        Initializes the locator.
        """
        super().__init__()
        self._label = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "rl-from-annotation"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Reference locator that uses the label to identify the annotation to use as reference data (returns OPEX bbox)."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-l", "--label", metavar="LABEL", type=str, help="The label of the annotation to use as reference data", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._label = ns.label

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()
        if result is None:
            if (self._label is None) or (len(self._label) == 0):
                result = "No label defined!"
        return result

    def _do_locate(self):
        """
        Attempts to locate the reference data.

        :return: the reference data, None if failed to do so
        :rtype: ObjectPrediction
        """
        result = None
        for obj in self.annotations.objects:
            if obj.label == self._label:
                result = obj
                break
        return result
