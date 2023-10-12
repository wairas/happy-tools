from ._object_region_extractor import ObjectRegionExtractor


class ObjectFromIDRegionExtractor(ObjectRegionExtractor):

    def __init__(self, object_key=None, region_size=(128, 128), target_name="THCA", objfunc=None):
        super().__init__(object_key, region_size=region_size, target_name=target_name)
        self.objfunc = objfunc

    def name(self) -> str:
        return "object-from-id-re"

    def description(self) -> str:
        return "TODO"

    def get_object_value(self, happy_data):
        return self.objfunc(happy_data.sample_id)
