class RegionExtractor:
    def __init__(self, region_size, target_name=None):
        self.target_name = target_name
        self.region_size = region_size

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
