import abc
import argparse
import os

from typing import Optional, Tuple
from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from seppl import split_args, split_cmdline, args_to_objects, get_class_name
from opex import ObjectPredictions


class AbstractReferenceLocator(PluginWithLogging, abc.ABC):
    """
    Ancestor for schemes that locate reference data.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self.parse_args([])

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        return None

    def _do_locate(self):
        """
        Attempts to locate the reference.

        :return: the suggested reference, None if failed to do so
        """
        raise NotImplementedError()

    def _post_check(self, ref) -> Tuple[Optional[str], Optional[str]]:
        """
        For checking the located reference.

        :param ref: the reference to object
        :return: the tuple of reference and message; the message is None if successful check, otherwise an error message
        :rtype: tuple
        """
        return ref, None

    def locate(self):
        """
        Attempts to locate the reference file using the supplied scan file.

        :return: the located reference, None if failed to locate
        """
        msg = self._pre_check()
        if msg is not None:
            raise Exception(msg)
        ref = self._do_locate()
        if ref is not None:
            ref, msg = self._post_check(ref)
            if msg is not None:
                raise Exception(msg)
        return ref

    @classmethod
    def parse_locator(cls, cmdline: str) -> 'AbstractReferenceLocator':
        """
        Splits the command-line, parses the arguments, instantiates and returns the black reference method.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the black ref plugin
        :rtype: AbstractBlackReferenceMethod
        """
        plugins = REGISTRY.ref_locators()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        plugins = args_to_objects(args, plugins, allow_global_options=False)
        if len(plugins) == 1:
            return plugins[0]
        else:
            raise Exception("Expected one reference locator plugin, but got %d from command-line: %s" % (len(plugins), cmdline))


class AbstractFileBasedReferenceLocator(AbstractReferenceLocator, abc.ABC):
    """
    Ancestor for reference locators that use files to locate the reference files.
    """

    def __init__(self):
        """
        Initializes the locator.
        """
        super().__init__()
        self._base_file = None
        self._must_exist = False

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-m", "--must_exist", action="store_true", help="Whether the determined reference file must exist", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._must_exist = ns.must_exist

    @property
    def base_file(self):
        """
        Returns the base file.

        :return: the base file
        :rtype: str
        """
        return self._base_file

    @base_file.setter
    def base_file(self, path):
        """
        Sets the base file to use.

        :param path: the base file
        :type path: str
        """
        self._base_file = path

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the file.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()

        if result is None:
            if self.base_file is None:
                result = "No base file set!"

        return result

    def _post_check(self, ref) -> Tuple[Optional[str], Optional[str]]:
        """
        For checking the located reference.

        :param ref: the reference to object
        :return: the tuple of reference and message; the message is None if successful check, otherwise an error message
        :rtype: tuple
        """
        ref, msg = super()._post_check(ref)

        if msg is None:
            if not os.path.exists(ref):
                if self._must_exist:
                    msg = "Reference file does not exist: %s" % ref
                else:
                    self.logger().warning("Reference file does not exist: %s" % ref)
                    ref = None

        return ref, msg


class AbstractAnnotationBasedReferenceLocator(AbstractReferenceLocator, abc.ABC):
    """
    Ancestor for reference locators that use annotations to locate the reference data.
    """

    def __init__(self):
        """
        Initializes the locator.
        """
        super().__init__()
        self._annotations = None

    @property
    def annotations(self):
        """
        Returns the annotations.

        :return: the annotations
        """
        return self._annotations

    @annotations.setter
    def annotations(self, ann):
        """
        Sets the annotations to use.

        :param ann: the annotations
        """
        self._annotations = ann

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()

        if result is None:
            if self.annotations is None:
                result = "No annotations set!"

        return result


class AbstractOPEXAnnotationBasedReferenceLocator(AbstractAnnotationBasedReferenceLocator, abc.ABC):
    """
    Ancestor for reference locators that use OPEX annotations to locate the reference data.
    """

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()

        if result is None:
            if not isinstance(self.annotations, ObjectPredictions):
                result = "Annotations are not derived from %s but: %s" % (get_class_name(ObjectPredictions), get_class_name(self.annotations))

        return result
