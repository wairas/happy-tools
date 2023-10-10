from happy.data import HappyData

from typing import List


class BaseReader:

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    def get_sample_ids(self) -> List[str]:
        raise NotImplementedError()

    def load_data(self, sample_id: str) -> List[HappyData]:
        raise NotImplementedError()

    def load_region(self, sample_id: str, region_name: str) -> HappyData:
        raise NotImplementedError()
