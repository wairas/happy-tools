import argparse
from ._region_extractor import RegionExtractor
from happy.criteria import Criteria, CriteriaGroup, OP_NOT_MISSING, OP_IN
from happy.preprocessors import CropPreprocessor


class ObjectRegionExtractor(RegionExtractor):

    def __init__(self, object_key=None, region_size=(128, 128), target_name=None, obj_values=None, base_criteria=[]):
        super().__init__(region_size, target_name)
        self.object_key = object_key
        self.obj_values = obj_values
        self.base_criteria = base_criteria

    def name(self) -> str:
        return "object-re"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        self._add_argparse_region_size(parser=parser, t=int, h="The width and height of the region", d=[128, 128])
        parser.add_argument("-k", "--object_key", type=str, help="The object key in the meta-data", required=False, default=None)
        # TODO type for obj_values other than str? extra option with choices?
        parser.add_argument("-o", "--obj_values", type=str, help="The object values to look for", required=False, nargs="*", default=[])
        parser.add_argument("-c", "--base_criteria", type=str, help="The criteria (in JSON notation) to apply", required=False, nargs="*", default=[])
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.truncate_regions = ns.truncate_regions
        self.object_key = ns.object_key
        # TODO convert strings to actual types?
        self.obj_values = ns.obj_values
        self.base_criteria = [Criteria.from_json(c) for c in ns.base_criteria]

    def get_object_value(self, happy_data):
        # TODO undefined member?
        return self.obj_name
        
    def _extract_regions(self, happy_data):
        object_values = self.obj_values
        if object_values is None:
            object_values = happy_data.get_unique_values(self.object_key)
        
        print(object_values)
      
        criteria_list = self.base_criteria
        if self.target_name is not None:
            criteria_list.extend([Criteria(OP_NOT_MISSING, key=self.target_name)])
        
        regions = []
        for obj_value in object_values:
            # Skip 0 value, which represents background
            
            object_criteria = criteria_list + [Criteria(OP_IN, key=self.object_key, value=[obj_value])]
            pixel_list, (centroid_x, centroid_y) = happy_data.find_pixels_with_criteria(CriteriaGroup(object_criteria))

            if len(pixel_list) == 0:
                continue
            
            # Determine center of the output region
            region_center_x = int(centroid_x)
            region_center_y = int(centroid_y)

            # Determine the size of the output region
            #region_size = 64  # example size, adjust as needed
            print(self.region_size)
            # Calculate the coordinates of the output region
            x_min = max(0, region_center_x - self.region_size[0] // 2)
            x_max = min(happy_data.width, region_center_x + self.region_size[0] // 2)
            y_min = max(0, region_center_y - self.region_size[1] // 2)
            y_max = min(happy_data.height, region_center_y + self.region_size[1] // 2)
            
            new_happy_data = happy_data.apply_preprocess(CropPreprocessor(x=x_min,y=y_min,width=x_max-x_min,height=y_max-y_min))
            
            new_happy_data.append_region_name(str(obj_value))
            regions.append(new_happy_data)
            #exit(0)
        return regions
    
    def add_target_data(self, regions):
        # already added by the region extractor
        return regions
