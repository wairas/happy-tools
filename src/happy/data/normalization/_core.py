import abc

from typing import Optional
from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from seppl import split_args, split_cmdline, args_to_objects, get_class_name
from opex import ObjectPredictions


CHANNEL_RED = 1
CHANNEL_GREEN = 2
CHANNEL_BLUE = 3


def channel_to_str(channel: int) -> str:
    """
    Turns the channel ID into a string representation.

    :param channel: the channel ID
    :type channel: int
    :return: the string representation
    :rtype: str
    """
    if channel == CHANNEL_RED:
        return "red"
    elif channel == CHANNEL_GREEN:
        return "green"
    elif channel == CHANNEL_BLUE:
        return "blue"
    else:
        raise Exception("Unsupported channel: %d" % channel)


class AbstractNormalization(PluginWithLogging, abc.ABC):
    """
    Ancestor for schemes that normalize the data for fake RGB images.
    Normalization applies to a single band.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self.parse_args([])

    def _pre_check(self, channel: int) -> Optional[str]:
        """
        Hook method that gets called before attempting to normalize data.

        :param channel: the channel to normalize
        :type channel: int
        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        if (channel != CHANNEL_RED) and (channel != CHANNEL_GREEN) and (channel != CHANNEL_BLUE):
            return "Unknown channel: %d" % channel
        return None

    def _do_normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to do so
        """
        raise NotImplementedError()

    def _post_check(self, data, channel: int) -> Optional[str]:
        """
        For checking the normalized data.

        :param data: the normalized data
        :param channel: the channel to normalize
        :type channel: int
        :return: None if successful check, otherwise error message
        :rtype: str
        """
        return None

    def normalize(self, data, channel: int):
        """
        Attempts to normalize the data.

        :param data: the data to normalize
        :param channel: the channel to normalize
        :type channel: int
        :return: the normalized data, None if failed to normalize
        """
        msg = self._pre_check(channel)
        if msg is not None:
            raise Exception(msg)
        result = self._do_normalize(data, channel)
        if result is not None:
            msg = self._post_check(result, channel)
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


class AbstractAnnotationBasedNormalization(AbstractNormalization, abc.ABC):
    """
    Ancestor for normalization schemes that use OPEX annotations to normalize the data.
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

    def _pre_check(self, channel: int) -> Optional[str]:
        """
        Hook method that gets called before attempting to normalize the data.

        :param channel: the channel to normalize
        :type channel: int
        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check(channel)

        if result is None:
            if self.annotations is None:
                result = "No annotations set!"

        return result


class AbstractOPEXAnnotationBasedNormalization(AbstractAnnotationBasedNormalization, abc.ABC):
    """
    Ancestor for normalization schemes that use OPEX annotations to normalize the data.
    """

    def _pre_check(self, channel: int) -> Optional[str]:
        """
        Hook method that gets called before attempting to locate the reference data.

        :param channel: the channel to normalize
        :type channel: int
        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check(channel)

        if result is None:
            if not isinstance(self.annotations, ObjectPredictions):
                result = "Annotations are not derived from %s but: %s" % (get_class_name(ObjectPredictions), get_class_name(self.annotations))

        return result
