from happy.region_extractors.region_extractor import RegionExtractor
from happy.preprocessors import CropPreprocessor


class GridRegionExtractor(RegionExtractor):
    def __init__(self, region_size, truncate_regions=False, target_name="THCA"):
        super().__init__(target_name, region_size)
        
        self.truncate_regions = truncate_regions

    def extract_regions_impl(self, happy_data):
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
