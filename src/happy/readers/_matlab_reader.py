import os

from typing import List, Optional, Tuple

import numpy as np

from happy.data import HappyData
from ._happydata_reader import HappyDataReader
from ._mat_reader import MatReader


class MatlabReader(HappyDataReader):

    def __init__(self, base_dir: str = None):
        super().__init__(base_dir=base_dir)

    def name(self) -> str:
        return "matlab-reader"

    def description(self) -> str:
        return "Reads data in HAPPy's Matlab format."

    def _get_sample_ids(self) -> List[str]:
        sample_ids = []
        for f in os.listdir(self.base_dir):
            if f.endswith(".mat"):
                sample_path = os.path.join(self.base_dir, f)
                if os.path.isfile(sample_path):
                    sample_id = os.path.splitext(f)[0]
                    sample_ids.append(sample_id)
        sample_ids = sorted(sample_ids)
        return sample_ids

    def _split_sample_id(self, sample_id: str) -> Tuple[str, Optional[str]]:
        parts = sample_id.split(".")
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            if len(parts[1]) == 0:
                return parts[0], None
            else:
                return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid sample_id format: {sample_id}")

    def _load_data(self, sample_id: str) -> List[HappyData]:
        sample_id, region_dir = self._split_sample_id(sample_id)
        return [self.load_region(sample_id, region_dir)]

    def _load_region(self, sample_id: str, region_name: str) -> HappyData:
        global_dict = {}
        metadata_dict = {}

        # read matlab
        reader = MatReader(
            self.base_dir,
            None,
            "normcube",
            wavelengths_struct="lambda"
        )
        reader.load_data("%s.%s" % (sample_id, region_name))

        # data
        data = reader.data

        # wavelengths
        wavelengths = reader.wavelengths

        # mask
        mask_meta = {}
        mask = reader.mat_file["FinalMask"]
        mask = np.expand_dims(mask, -1)  # add third dimension for envi
        mask_meta["data"] = mask
        mapping = {}
        for i in np.unique(mask):
            mapping[str(i)] = int(i)
        mask_meta["mapping"] = mapping
        metadata_dict["mask"] = mask_meta

        # assemble data
        result = HappyData(sample_id, region_name, data, global_dict, metadata_dict, wavenumbers=wavelengths)
        return result
