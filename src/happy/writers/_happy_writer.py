import json
import os

from happy.data import HappyData
from happy.writers.base import EnviWriter
from ._happydata_writer import HappyDataWriter


class HappyWriter(HappyDataWriter):

    def name(self) -> str:
        return "happy-writer"

    def description(self) -> str:
        return "Writes data in HAPPy format."

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        self.logger().info(f"write_data: datatype_mapping={datatype_mapping}")
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_single_data(happy_data_or_list, datatype_mapping)

    def get_datatype_mapping_for(self, datatype_mapping, outputname):
        if datatype_mapping is None:
            return None
        if outputname not in datatype_mapping:
            return None
        return datatype_mapping[outputname]
        
    def _write_single_data(self, happy_data, datatype_mapping=None):
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id

        # Create a folder for the sample if it doesn't exist
        sample_dir = os.path.join(self.base_dir, sample_id)
        os.makedirs(sample_dir, exist_ok=True)

        # Create a folder for the region if it doesn't exist
        region_dir = os.path.join(sample_dir, region_id)
        os.makedirs(region_dir, exist_ok=True)

        
        # Write hyperspectral data
        hyperspec_file_path = os.path.join(region_dir, f"{sample_id}.hdr")
        envi_writer = EnviWriter(region_dir)
        envi_writer.write_data(happy_data.data, hyperspec_file_path, datatype=self.get_datatype_mapping_for(datatype_mapping, sample_id), wavelengths=happy_data.wavenumbers)
        self.logger().info(f"data shape: {happy_data.data.shape}")

        # Write hyperspectral metadata (global)
        hyperspec_metadata_file = os.path.join(region_dir, f"{sample_id}_global.json")
        self.logger().info("region_dir: %s" % region_dir)
        self.logger().info("global_dict: %s" % str(happy_data.global_dict))
        with open(hyperspec_metadata_file, 'w') as f:
            json.dump(happy_data.global_dict, f)

        # Write other metadata
        for target_name, target_data in happy_data.metadata_dict.items():
            self.logger().info(f"target: {target_name}")
            metadata_file_path = os.path.join(region_dir, f"{target_name}.hdr")
            envi_writer.write_data(target_data['data'], metadata_file_path, datatype=self.get_datatype_mapping_for(datatype_mapping, target_name))

            # Write mapping if available
            mapping = target_data.get('mapping')
            if mapping:
                mapping_json_file = os.path.join(region_dir, f"{target_name}.json")
                with open(mapping_json_file, 'w') as f:
                    json.dump(mapping, f)
