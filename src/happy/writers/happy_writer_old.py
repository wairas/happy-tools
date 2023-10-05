import os
from happy.writers.envi_writer import EnviWriter
from happy.data import HappyData
from PIL import Image
import json


class HappyWriter:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def write_data(self, happy_data_or_list):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_single_data(happy_data)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_single_data(happy_data_or_list)
        else:
            raise ValueError("Input should be either a HappyData object or a list of HappyData objects.")

    def _write_single_data(self, happy_data):
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id

        # Create a folder for the sample if it doesn't exist
        sample_dir = os.path.join(self.base_dir, sample_id)
        os.makedirs(sample_dir, exist_ok=True)

        # Create a folder for the region if it doesn't exist
        region_dir = os.path.join(sample_dir, region_id)
        os.makedirs(region_dir, exist_ok=True)

        # Write Envi data
        envi_writer = EnviWriter(region_dir)
        envi_writer.write(happy_data.data, sample_id + '.hdr')

        # Write pixel metadata
        pixel_json_file = os.path.join(region_dir, sample_id + '_pixels.json')
        with open(pixel_json_file, 'w') as f:
            json.dump(happy_data.pixel_dict, f)

        # Write global metadata
        global_json_file = os.path.join(region_dir, sample_id + '_global.json')
        with open(global_json_file, 'w') as f:
            json.dump(happy_data.global_dict, f)
        
        # Write PNG data
        for key, png_array in happy_data.png_meta_data.items():
            png_path = os.path.join(region_dir, key + '.png')
            img = Image.fromarray(png_array)
            img.save(png_path)