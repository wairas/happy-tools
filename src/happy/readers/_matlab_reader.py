import os

from typing import List, Optional, Tuple

import numpy as np
import scipy.io as sio

from happy.data import HappyData
from ._happydata_reader import HappyDataReader


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
        filename = os.path.join(self.base_dir, "%s.%s.mat" % (sample_id, region_name))
        mat_file = sio.loadmat(filename)

        # data
        data = mat_file["normcube"]

        # wavelengths
        wavelengths = mat_file["lambda"]
        if wavelengths is None:
            arr = data[0, 0, :]
            wavelengths = np.arange(arr.size)

        # mask
        if "FinalMask" in mat_file:
            mask_meta = {}
            mask = mat_file["FinalMask"]
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
