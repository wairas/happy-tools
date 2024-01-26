import argparse

from typing import List

from ._preprocessor import Preprocessor
from happy.data import HappyData
from happy.region_extractors import RegionExtractor


class ExtractRegionsPreprocessor(Preprocessor):

    def name(self) -> str:
        return "extract-regions"

    def description(self) -> str:
        return "Applies the specified region extractor to extract (sub-)regions from the incoming data."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-r", "--region_extractor", type=str, help="The command-line of the region-extractor to apply", required=False, default="re-full")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["region_extractor"] = ns.region_extractor

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        cmdline = self.params.get("region_extractor", "re-full")
        self.logger().info("extractor cmdline: %s" % cmdline)
        region_extractor = RegionExtractor.parse_region_extractor(cmdline)
        return region_extractor.extract_regions(happy_data)
