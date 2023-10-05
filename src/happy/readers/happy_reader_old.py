import numpy as np
import os
from happy.readers.envi_reader import EnviReader
from happy.readers.json_reader import JsonReader
from happy.data import HappyData
from PIL import Image


class HappyReader:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def split_sample_id(self, sample_id):
        parts = sample_id.split(":")
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid sample_id format: {sample_id}")
            
    def get_regions(self, sample_id):
        sample_dir = os.path.join(self.base_dir, sample_id)
        region_dirs = [name for name in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, name))]
        return region_dirs
        
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
        # Load the Envi data for the given region
        envi_dir = os.path.join(self.base_dir, sample_id, region_name)
        envi_reader = EnviReader(envi_dir, None)
        envi_reader.load_data(sample_id)

        # Load the Json data for the given region
        json_dir = os.path.join(self.base_dir, sample_id, region_name)
        json_reader = JsonReader(json_dir, sample_id)
        json_reader.load_pixel_json()
        json_reader.load_global_json()

       # Load all PNG data in the region folder
        png_dir = os.path.join(self.base_dir, sample_id, region_name)
        png_files = [f for f in os.listdir(png_dir) if f.endswith(".png")]
        png_data = {filename[:-4]: self.load_png_data(os.path.join(png_dir, filename)) for filename in png_files}

        # Create HappyData object for this region
        happy_data = HappyData(sample_id, region_name, envi_reader.get_numpy(), json_reader.get_pixel_dict(), json_reader.get_global_dict(), envi_reader.get_wavelengths(), png_data)

        return happy_data

    def load_png_data(self, png_path):
        png_image = Image.open(png_path)
        return np.array(png_image)
        