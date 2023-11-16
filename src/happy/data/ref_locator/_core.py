import abc
import os

from typing import Optional
from happy.base.registry import REGISTRY
from seppl import Plugin, split_args, split_cmdline, args_to_objects


class AbstractReferenceLocator(Plugin, abc.ABC):
    """
    Ancestor for schemes that locate reference data.
    """

    def _check(self, scan_file: str) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the file.

        :param scan_file: the scan file to use for locating
        :type scan_file: str
        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        return None

    def _do_locate(self, scan_file: str) -> Optional[str]:
        """
        Attempts to locate the reference file using the supplied scan file.

        :param scan_file: the scan file to use as basis for locating the reference
        :type scan_file: str
        :return: the suggested reference file name, None if failed to do so
        :rtype: str
        """
        raise NotImplementedError()

    def locate(self, scan_file: str, must_exist: bool = False) -> Optional[str]:
        """
        Attempts to locate the reference file using the supplied scan file.

        :param scan_file: the scan file to use as basis for locating the reference
        :type scan_file: str
        :param must_exist: whether the file must exist, returns None if it doesn't exist
        :type must_exist: bool
        :return: the suggested reference file name, None if failed to do so
        :rtype: str
        """
        msg = self._check(scan_file)
        if msg is not None:
            raise Exception(msg)
        result = self._do_locate(scan_file)
        if (result is not None) and must_exist and (not os.path.exists(result)):
            result = None
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

    @classmethod
    def apply_locator(cls, cmdline: str, scan_file: str, must_exist: bool = False) -> Optional[str]:
        """
        Parses the locator commandline and applies it to the scan file to locate the reference.

        :param cmdline: the command-line to process
        :type cmdline: str
        :param scan_file: the scan file to use as basis for locating the reference
        :type scan_file: str
        :param must_exist: whether the file must exist, returns None if it doesn't exist
        :type must_exist: bool
        :return: the suggested reference file name, None if failed to do so
        :rtype: str
        """
        locator = cls.parse_locator(cmdline)
        return locator.locate(scan_file, must_exist=must_exist)
