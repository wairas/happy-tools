from ._region_extractor import RegionExtractor


class FullRegionExtractor(RegionExtractor):

    def __init__(self, region_size=None, target_name=None):
        super().__init__(region_size=region_size, target_name=target_name)

    def name(self) -> str:
        return "full-re"

    def description(self) -> str:
        return "TODO"

    def _extract_regions(self, happy_data):
        # Return the input happy_data object as one region without any cropping
        return [happy_data]
