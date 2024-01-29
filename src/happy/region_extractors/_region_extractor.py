import abc
import argparse
import os

from typing import Optional, List
from seppl import split_args, split_cmdline, args_to_objects
from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from happy.data import HappyData


class RegionExtractor(PluginWithLogging, abc.ABC):

    def __init__(self, region_size=None, target_name: str = None):
        super().__init__()
        self.target_name = target_name
        self.region_size = region_size

    def _add_argparse_region_size(self, parser: argparse.ArgumentParser, t, h: str, d, nargs=None):
        """
        Adds the region_size parameter to the parser.

        :param parser: the parser to update
        :type parser: argparse.ArgumentParser
        :param t: the type of the parameter
        :param h: the help text
        :type h: str
        :param d: the default value
        :param nargs: the nargs definition, eg "+"/"*"/2
        """
        parser.add_argument("-r", "--region_size", type=t, help=h, required=(d is None), default=d, nargs=nargs)

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-t", "--target_name", type=str, help="The name of the target value", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.target_name = ns.target_name
        self.region_size = None
        if "region_size" in ns:
            self.region_size = ns.region_size

    def is_compatible(self, region: 'RegionExtractor') -> bool:
        return self.region_size == region.region_size
    
    def extract_regions(self, happy_data: HappyData) -> List[HappyData]:
        # Get metadata for target names    
        regions = self._extract_regions(happy_data)
        regions = self.add_target_data(regions)
        # TODO add processing note
        return regions

    def _extract_regions(self, happy_data: HappyData) -> List[HappyData]:
        raise NotImplementedError()

    def add_target_data(self, regions: List[HappyData]) -> List[HappyData]:
        return regions

    @classmethod
    def parse_region_extractor(cls, cmdline: str) -> Optional['RegionExtractor']:
        """
        Splits the command-line, parses the arguments, instantiates and returns the region extractor.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the region extractors, None if not exactly one selector parsed
        :rtype: RegionExtractor
        """
        plugins = REGISTRY.region_extractors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        l = args_to_objects(args, plugins, allow_global_options=False)
        if len(l) == 1:
            return l[0]
        else:
            return None

    @classmethod
    def parse_region_extractors(cls, cmdline: str) -> List:
        """
        Splits the command-line, parses the arguments, instantiates and returns the region extractors.
        If pointing to a file, reads one region extractors per line, instantiates and returns them.
        Empty lines or lines starting with # get ignored.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the region extractor plugin list
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
                    pp = cls.parse_region_extractor(line.strip())
                    if pp is not None:
                        result.append(pp)
            return result
        else:
            plugins = REGISTRY.region_extractors()
            args = split_args(split_cmdline(cmdline), plugins.keys())
            return args_to_objects(args, plugins, allow_global_options=False)
