import argparse
import numpy as np

from ._core import AbstractFileBasedWhiteReferenceMethod


class WhiteReferenceAnnotationAverage(AbstractFileBasedWhiteReferenceMethod):
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
        return "Computes the average per band in the annotation rectangle. Does not require scan and reference to have the same size."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-a", "--annotation", metavar="COORD", type=int, help="The annotation rectangle (top, left, bottom, right)", required=False, nargs=4)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._annotation = ns.annotation

    @property
    def annotation(self):
        """
        Returns the current white reference annotation.

        :return: the white reference annotation tuple (top, left, bottom, right)
        :rtype: tuple
        """
        return self._reference

    @annotation.setter
    def annotation(self, ann):
        """
        Sets the white reference annotation tuple to use.

        :param ann: the annotation tuple to use (top, left, bottom, right)
        :type ann: tuple
        """
        self._annotation = ann
        self._reset()

    def _do_initialize(self):
        """
        Hook method for initializing the white reference method.
        """
        super()._do_initialize()
        if self._annotation is None:
            raise Exception("No annotation set (top, left, bottom, right)!")
        if not isinstance(self._annotation, tuple):
            raise Exception("Annotation is not a tuple: %s" % str(type(self._annotation)))
        if not len(self._annotation) == 4:
            raise Exception("Annotation tuple has wrong length (expected 4): %d" % len(self._annotation))

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        top, left, bottom, right = self._annotation
        whiteref = scan[top:bottom, left:right, :]
        num_bands = scan.shape[2]
        whiteref_annotation = []
        for i in range(num_bands):
            whiteref_annotation.append(np.average(whiteref[:, :, i]))
        result = scan.copy()
        for i in range(len(whiteref_annotation)):
            if whiteref_annotation[i] != 1.0:
                result[:, :, i] = result[:, :, i] / whiteref_annotation[i]
        return result
