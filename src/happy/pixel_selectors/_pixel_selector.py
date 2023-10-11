import abc

from happy.base.core import ConfigurableObject
from happy.base.registry import REGISTRY
from seppl import Plugin, split_args, split_cmdline, args_to_objects


class PixelSelector(ConfigurableObject, Plugin, abc.ABC):

    def get_n(self):
        raise NotImplementedError()

    def get_all_pixels(self, happy_data):
        return self.select_pixels(happy_data, n=-1)

    def select_pixels(self, happy_data, n=None):
        raise NotImplementedError()

    @classmethod
    def parse_pixel_selector(cls, cmdline):
        """
        Splits the command-line, parses the arguments, instantiates and returns the pixel selectro.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the pixel selector
        :rtype: PixelSelector
        """
        plugins = REGISTRY.pixel_selectors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        return args_to_objects(args, plugins, allow_global_options=False)
