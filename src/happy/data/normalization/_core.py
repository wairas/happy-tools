import abc

from typing import Optional
from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from seppl import split_args, split_cmdline, args_to_objects, get_class_name
from opex import ObjectPredictions


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

    def _pre_check(self) -> Optional[str]:
        """
        Hook method that gets called before attempting to normalize the data.

        :return: the result of the check, None if successful otherwise error message
        :rtype: str
        """
        result = super()._pre_check()

        if result is None:
            if self.annotations is None:
                result = "No annotations set!"

        return result


class AbstractOPEXAnnotationBasedNormalization(AbstractAnnotationBasedNormalization, abc.ABC):
    """
    Ancestor for normalization schemes that use OPEX annotations to normalize the data.
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
