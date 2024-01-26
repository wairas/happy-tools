from typing import List

from happy.data import HappyData
from ._region_extractor import RegionExtractor


class FullRegionExtractor(RegionExtractor):

    def __init__(self, region_size=None, target_name: str = None):
        super().__init__(region_size=region_size, target_name=target_name)

    def name(self) -> str:
        return "re-full"

    def description(self) -> str:
        return "Returns the input as-is without any cropping."

    def _extract_regions(self, happy_data: HappyData) -> List[HappyData]:
        return [happy_data]
