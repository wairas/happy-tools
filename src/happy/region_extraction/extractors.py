import json
import numpy as np
import os
import scipy.io as sio


class RegionExtractor:
    def __init__(self, reader, target_names=None):
        self.reader = reader
        self.target_names = target_names

    def extract_regions(self, id):
        # Get metadata for target names
        regions = self.extract_regions_impl(id)
        regions = self.add_target_data(regions)
        return regions

    def extract_regions_impl(self, id):
        raise NotImplementedError("Subclasses must implement extract_regions_impl")

    def add_target_data(self, regions):
        metadata = {}
        if self.target_names is not None:
            for target_name in self.target_names:
                metadata[target_name] = self.reader.json_reader.get_meta_data(key=target_name)
        for region_meta, region_data in regions:
            region_meta['target_data'] = metadata
        return regions


class MaskRegionExtractor(RegionExtractor):
    def __init__(self, reader, mask_dir, types, target_names=None):
        self.mask_dir = mask_dir
        self.types = types
        super().__init__(reader, target_names)

    def extract_regions_impl(self, id):
        mask_path = os.path.join(self.mask_dir, f"{id}.mat")
        mask_file = sio.loadmat(mask_path)
        mask = mask_file['FinalMask']
        full_image = self.reader.get_numpy()
        regions = []
        for type in self.types:
            indices = np.where(mask == type)
            if len(indices[0]) > 0:
                x_min, x_max = int(np.min(indices[1])), int(np.max(indices[1]))
                y_min, y_max = int(np.min(indices[0])), int(np.max(indices[0]))
                region_name = f"{type}_region"
                region_meta = {'region_name': region_name, 'x': x_min, 'y': y_min, 'w': x_max - x_min + 1, 'h': y_max - y_min + 1}
                region_data = full_image[y_min:y_max + 1, x_min:x_max + 1]
                # print(region_data.shape)
                regions.append((region_meta, region_data))

        return regions


class FullRegionExtractor(RegionExtractor):
    def __init__(self, reader, target_names=None):
        super().__init__(reader, target_names)

    def extract_regions_impl(self, id):
        full_image = self.reader.get_numpy()

        # Default behavior is to return full image as one region
        regions = [({'region_name': 'full_image', 'x': 0, 'y': 0, 'w': full_image.shape[1], 'h': full_image.shape[0]}, full_image)]

        return regions


class ObjectRegionExtractor(RegionExtractor):
    def __init__(self, reader, object_name, region_size=128, target_names=["THCA"], objfunc=None):
        super().__init__(reader, target_names)
        self.object_name = object_name
        self.region_size = region_size
        self.objfunc = objfunc

    def extract_regions_impl(self, id):
        full_image = self.reader.get_numpy()

        object_image = self.reader.get_numpy_of(self.object_name)
        print(self.object_name)
        print(full_image.shape)
        print(object_image.shape)

        # Get unique object values from the object image
        if self.objfunc is None:
            object_values = np.unique(object_image)
        else:
            object_values =[self.objfunc(id)]

        print(object_values)
        regions = []
        for obj_value in object_values:
            # Skip 0 value, which represents background
            if obj_value == 0:
                continue
            print(obj_value)

            # Create a mask to extract region corresponding to the object value
            obj_mask = (object_image == obj_value)
            region_data = full_image.copy()
            region_data[obj_mask == 0] = 0  # Set non-object pixels to 0

            num_nonzero = np.count_nonzero(region_data)

            # Print the result
            print("Number of non-zero pixels:", num_nonzero)

            # Extract non-zero x, y coordinates
            y, x = np.argwhere(obj_mask > 0).T

            centroid_x = np.mean(x)
            centroid_y = np.mean(y)

            # Determine center of the output region
            region_center_x = int(centroid_x)
            region_center_y = int(centroid_y)

            # Determine the size of the output region
            # region_size = 64  # example size, adjust as needed
            print(self.region_size)
            # Calculate the coordinates of the output region
            x_min = max(0, region_center_x - self.region_size // 2)
            x_max = min(full_image.shape[1], region_center_x + self.region_size // 2)
            y_min = max(0, region_center_y - self.region_size // 2)
            y_max = min(full_image.shape[0], region_center_y + self.region_size // 2)

            # Create region metadata
            region_name = f"object_{obj_value}_region"
            region_meta = {
                'region_name': region_name,
                'x': x_min,
                'y': y_min,
                'w': x_max - x_min + 1,
                'h': y_max - y_min + 1,
                "xpos": int(x[0]),
                "ypos": int(y[0])
            }
            tdic = region_meta['target_data'] = {}
            if self.target_names is not None:
                for target_name in self.target_names:
                    tdic[target_name] = self.reader.json_reader.get_meta_data(key=target_name ,x=x[0], y=y[0])
                    tdic[target_name + "_rev"] = self.reader.json_reader.get_meta_data(key=target_name, x=y[0], y=x[0])
                    if tdic[target_name] is not None and tdic[target_name] > 0:
                        region_data = region_data[y_min:y_max, x_min:x_max].copy()
                        regions.append((region_meta, region_data))
                        print("shape:", region_data.shape)
        return regions


class JSONRegionExtractor(RegionExtractor):
    def __init__(self, reader, json_file, target_names=None):
        super().__init__(reader, target_names)
        self.json_file = json_file

    def extract_regions_impl(self, id):
        full_image = self.reader.get_numpy()

        with open(self.json_file) as f:
            data = json.load(f)

        regions = []
        for region in data:
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            regions.append(({'region_name': region['name'], 'x': x, 'y': y, 'w': w, 'h': h}, full_image))

        return regions
