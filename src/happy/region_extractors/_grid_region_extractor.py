import argparse
from ._region_extractor import RegionExtractor
from happy.preprocessors import CropPreprocessor


class GridRegionExtractor(RegionExtractor):

    def __init__(self, region_size=None, truncate_regions=False, target_name="THCA"):
        super().__init__(target_name=target_name, region_size=region_size)
        self.truncate_regions = truncate_regions

    def name(self) -> str:
        return "grid-re"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        self._add_argparse_region_size(parser=parser, t=int, h="The width and height of the region", d=None)
        parser.add_argument("-T", "--truncate_regions", action="store_true", help="Whether to truncate the regions", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.truncate_regions = ns.truncate_regions

    def _extract_regions(self, happy_data):
        regions = []

        width, height = happy_data.width, happy_data.height

        for y in range(0, height, self.region_size[1]):
            for x in range(0, width, self.region_size[0]):
                x_min, x_max = x, x + self.region_size[0]
                y_min, y_max = y, y + self.region_size[1]

                # Truncate regions if they go off the end
                if self.truncate_regions:
                    x_max = min(x_max, width)
                    y_max = min(y_max, height)

                # Skip regions that go off the end
                if x_min >= width or y_min >= height:
                    continue

                new_happy_data = happy_data.apply_preprocess(CropPreprocessor(x=x_min, y=y_min, width=x_max - x_min, height=y_max - y_min))
                new_happy_data.append_region_name(str(len(regions)))
                regions.append(new_happy_data)

        return regions
