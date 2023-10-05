from ._object_region_extractor import ObjectRegionExtractor


class ObjectFromIDRegionExtractor(ObjectRegionExtractor):
    def __init__(self, object_key, region_size=128, target_name="THCA", objfunc=None):
        super().__init__(object_key, region_size=region_size, target_name=target_name, obj_name=None)
        self.objfunc = objfunc

    def get_object_value(self, happy_data):
        return self.objfunc(happy_data.sample_id)
