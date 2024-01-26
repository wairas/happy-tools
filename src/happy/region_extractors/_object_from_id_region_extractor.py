from ._object_region_extractor import ObjectRegionExtractor
from happy.data import HappyData


class ObjectFromIDRegionExtractor(ObjectRegionExtractor):

    def __init__(self, object_key=None, region_size=(128, 128), target_name: str = "THCA", objfunc=None):
        super().__init__(object_key, region_size=region_size, target_name=target_name)
        self.objfunc = objfunc

    def name(self) -> str:
        return "re-object-from-id"

    def description(self) -> str:
        return "TODO"

    def get_object_value(self, happy_data: HappyData):
        return self.objfunc(happy_data.sample_id)
