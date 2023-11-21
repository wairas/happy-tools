import abc
import argparse
import os

from typing import Optional
from happy.base.registry import REGISTRY
from seppl import Plugin, split_args, split_cmdline, args_to_objects


class AbstractReferenceLocator(Plugin, abc.ABC):
    """
    Ancestor for schemes that locate reference data.
    """

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

    def _post_check(self, ref) -> Optional[str]:
        """
        For checking the located reference.

        :param ref: the reference to object
        :return: None if successful check, otherwise error message
        :rtype: str
        """
        return None

    def locate(self):
        """
        Attempts to locate the reference file using the supplied scan file.

        :return: the located reference, None if failed to locate
        """
        msg = self._pre_check()
        if msg is not None:
            raise Exception(msg)
        result = self._do_locate()
        if result is not None:
            msg = self._post_check(result)
            if msg is not None:
                raise Exception(msg)
        return result

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

    def _post_check(self, ref) -> Optional[str]:
        """
        For checking the located reference.

        :param ref: the reference to object
        :return: None if successful check, otherwise error message
        :rtype: str
        """
        result = super()._post_check(ref)

        if result is None:
            if self._must_exist and not os.path.exists(ref):
                result = "Reference file does not exist: %s" % ref

        return result
