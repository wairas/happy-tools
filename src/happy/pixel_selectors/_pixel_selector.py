import abc

from happy.base.core import ConfigurableObject
from happy.base.registry import REGISTRY
from seppl import Plugin, split_args, split_cmdline, args_to_objects
from typing import List, Optional


class PixelSelector(ConfigurableObject, Plugin, abc.ABC):

    def get_n(self):
        raise NotImplementedError()

    def get_all_pixels(self, happy_data):
        return self.select_pixels(happy_data, n=-1)

    def select_pixels(self, happy_data, n=None):
        raise NotImplementedError()

    @classmethod
    def parse_pixel_selector(cls, cmdline: str) -> Optional['PixelSelector']:
        """
        Splits the command-line, parses the arguments, instantiates and returns the pixel selector.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the pixel selector, None if not exactly one selector parsed
        :rtype: PixelSelector
        """
        plugins = REGISTRY.pixel_selectors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        l = args_to_objects(args, plugins, allow_global_options=False)
        if len(l) == 1:
            return l[0]
        else:
            return None

    @classmethod
    def parse_pixel_selectors(cls, cmdline: str) -> List['PixelSelector']:
        """
        Splits the command-line, parses the arguments, instantiates and returns the pixel selectors.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the list of pixel selectors
        :rtype: list
        """
        plugins = REGISTRY.pixel_selectors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        return args_to_objects(args, plugins, allow_global_options=False)
