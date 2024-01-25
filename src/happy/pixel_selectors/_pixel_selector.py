import abc
import os

from happy.base.core import ConfigurableObject, PluginWithLogging
from happy.base.registry import REGISTRY
from seppl import split_args, split_cmdline, args_to_objects
from typing import List, Optional


class PixelSelector(ConfigurableObject, PluginWithLogging, abc.ABC):

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self.parse_args([])

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
        If pointing to a file, reads one pixel selector per line, instantiates and returns them.
        Empty lines or lines starting with # get ignored.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the list of pixel selectors
        :rtype: list
        """
        if os.path.exists(cmdline) and os.path.isfile(cmdline):
            result = []
            with open(cmdline) as fp:
                for line in fp.readlines():
                    line = line.strip()
                    # empty?
                    if len(line) == 0:
                        continue
                    # comment?
                    if line.startswith("#"):
                        continue
                    ps = cls.parse_pixel_selector(line)
                    if ps is not None:
                        result.append(ps)
            return result
        else:
            plugins = REGISTRY.pixel_selectors()
            args = split_args(split_cmdline(cmdline), plugins.keys())
            return args_to_objects(args, plugins, allow_global_options=False)
