import abc

from typing import Optional
from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from seppl import split_args, split_cmdline, args_to_objects


class AbstractNormalization(PluginWithLogging, abc.ABC):
    """
    Ancestor for schemes that normalize the data for fake RGB images.
    """

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to normalize data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        return None

    def _do_normalize(self, data):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :return: the normalized data, None if failed to do so
        """
        raise NotImplementedError()

    def _post_check(self, data) -> Optional[str]:
        """
        For checking the normalized data.

        :param data: the normalized data
        :return: None if successful check, otherwise error message
        :rtype: str
        """
        return None

    def normalize(self, data):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :return: the normalized data, None if failed to normalize
        """
        msg = self._pre_check()
        if msg is not None:
            raise Exception(msg)
        result = self._do_normalize(data)
        if result is not None:
            msg = self._post_check(result)
            if msg is not None:
                raise Exception(msg)
        return result

    @classmethod
    def parse_normalization(cls, cmdline: str) -> 'AbstractNormalization':
        """
        Splits the command-line, parses the arguments, instantiates and returns the black reference method.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the black ref plugin
        :rtype: AbstractBlackReferenceMethod
        """
        plugins = REGISTRY.normalizations()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        plugins = args_to_objects(args, plugins, allow_global_options=False)
        if len(plugins) == 1:
            return plugins[0]
        else:
            raise Exception("Expected one normalization plugin, but got %d from command-line: %s" % (len(plugins), cmdline))
