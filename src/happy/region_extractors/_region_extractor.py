import abc
import argparse

from seppl import Plugin


class RegionExtractor(Plugin, abc.ABC):

    def __init__(self, region_size=None, target_name=None):
        self.target_name = target_name
        self.region_size = region_size

    def _add_argparse_region_size(self, parser, t, h, d):
        parser.add_argument("-r", "--region_size", type=t, help=h, required=(d is None), default=d)

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

    def is_compatible(self, region):
        return self.region_size == region.region_size
    
    def extract_regions(self, happy_data):
        # Get metadata for target names    
        regions = self._extract_regions(happy_data)
        regions = self.add_target_data(regions)           
        return regions

    def _extract_regions(self, id):
        raise NotImplementedError("Subclasses must implement extract_regions_impl")
        
    def add_target_data(self, regions):
        return regions
