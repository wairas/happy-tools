import os
import json


class JsonReader:
    def __init__(self, json_dir, sample_id):
        self.json_dir = json_dir
        self.global_dict = {}
        self.pixel_dict = {}
        self.sample_id = sample_id

    def load_json(self, file_name):
        file_path = os.path.join(self.json_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Error: {file_path} does not exist.")
            return {}
        with open(file_path) as f:
            json_dict = json.load(f)
        return json_dict

    def get_meta_data(self, x=None, y=None, key="type"):
        if key == "x":
            return x
        elif key == "y":
            return y
        x = str(x)
        if x in self.pixel_dict:
            y = str(y)
            if y in self.pixel_dict[x]:
                if key in self.pixel_dict[x][y]:
                    return self.pixel_dict[x][y][key]
        return self.get_meta_global_data(key)
        
    def get_meta_global_data(self, key):
        if key in self.global_dict:
            return self.global_dict[key]
        elif key in self.global_dict["meta_data"]:
            return self.global_dict["meta_data"][key]
        else:
            return None
    
    def load_pixel_json(self):
        pixel_json = self.load_json(self.sample_id+'_pixels.json')
        self.pixel_dict = pixel_json

    def load_global_json(self):
        global_json = self.load_json(self.sample_id+'_global.json')
        self.global_dict = global_json
        
    def get_pixel_dict(self):
        return self.pixel_dict

    def get_global_dict(self):
        return self.global_dict

    def set_pixel_dict(self, pixel_dict):
        self.pixel_dict = pixel_dict

    def set_global_dict(self, global_dict):
        self.global_dict = global_dict
