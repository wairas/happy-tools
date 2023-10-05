import os
import json
import numpy as np
from happy.readers.envi_reader import EnviReader
from happy.data import HappyData
import spectral.io.envi as envi

ENVI_DTYPE_TO_NUMPY = {
    1: 'uint8',
    2: 'int16',
    3: 'int32',
    4: 'float32',
    5: 'float64',
    12: 'uint16',
    13: 'uint32',
    14: 'complex64',
    15: 'complex128'
}


class HappyReader:
    def __init__(self, base_dir, restrict_metadata=None):
        self.base_dir = base_dir
        self.restrict_metadata = restrict_metadata

    def get_sample_ids(self):
        sample_ids = []
        for sample_id in os.listdir(self.base_dir):
            sample_path = os.path.join(self.base_dir, sample_id)
            if os.path.isdir(sample_path):
                sample_ids.append(sample_id)
        return sample_ids
        
    def split_sample_id(self, sample_id):
        parts = sample_id.split(":")
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid sample_id format: {sample_id}")

    def load_data(self, sample_id):
        sample_id, region_dir = self.split_sample_id(sample_id)

        if region_dir is not None:
            return [self.load_region(sample_id, region_dir)]

        happy_data_list = []
        for region_dir in self.get_regions(sample_id):
            happy_data = self.load_region(sample_id, region_dir)
            happy_data_list.append(happy_data)

        return happy_data_list

    def load_region(self, sample_id, region_name):
        hyperspec_file_path = os.path.join(self.base_dir, sample_id, region_name, f'{sample_id}'+".hdr")
        print(f"{sample_id}:{region_name}")
        base_path = os.path.join(self.base_dir, sample_id, region_name)

        if os.path.exists(hyperspec_file_path):
            envi_reader = EnviReader(base_path, None)
            envi_reader.load_data(sample_id)
            hyperspec_data = envi_reader.get_numpy()

            # Load hyperspec metadata and mappings
            hyperspec_metadata = self.load_json(hyperspec_file_path.replace(".hdr", "_global.json"))
            metadata_dict = {}
            for metadata_file_path in self.get_metadata_file_paths(base_path):
                target_name = os.path.splitext(os.path.basename(metadata_file_path))[0]
                if target_name == sample_id:
                    continue
                metadata = self.load_target_metadata(base_path, target_name)
                json_mapping_path = metadata_file_path.replace(".hdr", ".json")
                mapping = self.load_json(json_mapping_path)
                metadata_dict[target_name] = {"data": metadata, "mapping": mapping}

            # Create HappyData object for this region
            happy_data = HappyData(sample_id, region_name, hyperspec_data, hyperspec_metadata, metadata_dict, envi_reader.get_wavelengths())

            return happy_data
        else:
            raise ValueError(f"Hyperspectral ENVI file not found for sample_id: {sample_id}")

    def load_target_metadata(self, base_dir, target):
        filename = os.path.join(base_dir,f'{target}'+".hdr")
        header = envi.read_envi_header(filename)
        data_type = header['data type']  
        open = envi.open(filename)
        data = open.load()
        return np.asarray(data, dtype=ENVI_DTYPE_TO_NUMPY[int(data_type)])
        
    def load_json(self, json_mapping_path):
        if os.path.exists(json_mapping_path):
            with open(json_mapping_path, 'r') as f:
                return json.load(f)
        else:
            return {}

    def get_metadata_file_paths(self, base_path):
        metadata_file_paths = []
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".hdr"):
                    if self.restrict_metadata is None or os.path.splitext(file)[0] in self.restrict_metadata:
                        metadata_file_paths.append(os.path.join(root, file))
        
        return metadata_file_paths

    def get_regions(self, sample_id):
        sample_dir = os.path.join(self.base_dir, sample_id)
        if os.path.isdir(sample_dir):
            region_dirs = [name for name in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, name))]
        else:
            region_dirs = []
        return region_dirs
