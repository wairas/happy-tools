from ._region_extractor import RegionExtractor


class FullRegionExtractor(RegionExtractor):
    def __init__(self, region_size, target_name=None):
        super().__init__(region_size, target_name)

    def extract_regions_impl(self, happy_data):
        # Return the input happy_data object as one region without any cropping
        return [happy_data]
