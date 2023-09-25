import os
import json
from happy.writers.envi_writer import EnviWriter
from happy.data.happy_data import HappyData


class HappyWriter:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def write_data(self, happy_data_or_list, datatype_mapping=None):
        print(f"write_data {datatype_mapping}")
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_single_data(happy_data,datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_single_data(happy_data_or_list, datatype_mapping)
        else:
            raise ValueError("Input should be either a HappyData object or a list of HappyData objects.")

    def get_datatype_mapping_for(self, datatype_mapping, outputname):
        #outputname = outputname.strip("'")
        #print(f"checking: {outputname!r}")
        #print(datatype_mapping)
        #for key in datatype_mapping:
            #print(f"Key repr: {key!r}")
        if datatype_mapping is None:
            #print("none")
            return None
        if outputname not in datatype_mapping:
            #print("not in")
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
        envi_writer.write_data(happy_data.data, hyperspec_file_path, datatype=self.get_datatype_mapping_for(datatype_mapping, sample_id))
        print(f"region happy data writer: {happy_data.data.shape}")

        # Write hyperspectral metadata (global)
        hyperspec_metadata_file = os.path.join(region_dir, f"{sample_id}_global.json")
        print(region_dir)
        print(happy_data.global_dict)
        with open(hyperspec_metadata_file, 'w') as f:
            json.dump(happy_data.global_dict, f)

        # Write other metadata
        for target_name, target_data in happy_data.metadata_dict.items():
            print(f"target: {target_name}")
            metadata_file_path = os.path.join(region_dir, f"{target_name}.hdr")
            envi_writer.write_data(target_data['data'], metadata_file_path, datatype=self.get_datatype_mapping_for(datatype_mapping, target_name))

            # Write mapping if available
            mapping = target_data.get('mapping')
            if mapping:
                mapping_json_file = os.path.join(region_dir, f"{target_name}.json")
                with open(mapping_json_file, 'w') as f:
                    json.dump(mapping, f)
