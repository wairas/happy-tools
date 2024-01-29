import copy
import numpy as np
import spectral.io.envi as envi

from typing import Dict, List, Tuple, Union, Optional

from spectral import SpyFile
from happy.criteria import Criteria, CriteriaGroup


MASK_MAP = "mask-map"


class HappyData:

    def __init__(self, sample_id: str, region_id: str, data: np.ndarray, global_dict: Dict, metadata_dict: Dict, wavenumbers: List = None):
        self.sample_id = sample_id
        self.region_id = region_id
        self.data = data
        self.global_dict = global_dict
        self.wavenumbers = wavenumbers
        self.width = self.data.shape[1]
        self.height = self.data.shape[0]
        self.metadata_dict = metadata_dict

    def get_full_id(self) -> str:
        return self.sample_id + ":" + self.region_id
        
    def append_region_name(self, to_append: str):
        self.region_id = self.region_id + "_" + to_append
        
    def get_unique_values(self, target: str) -> List:
        if target not in self.metadata_dict:
            return []

        data = self.metadata_dict[target]["data"]
        unique_values = np.unique(data)
        unique_values_list = unique_values.tolist()
        return unique_values_list

    """    
    def get_segmentation_labels(self, target, mapping):
        if target in self.metadata_dict:
            return self.metadata_dict[target]["data"], self.metadata_dict[target]["mapping"]
            
        return None, None
    """    
        
    def find_pixels_with_criteria(self, criteria: Union[Criteria, CriteriaGroup], calculate_centroid: bool = True) -> Tuple[List[Tuple], Tuple]:
        x_coords = []
        y_coords = []
        valid_xy_pairs = []
        return_pairs = []
        
        key_list = criteria.get_keys()
        print("kl")
        print(key_list)
        print("--")
        print(criteria)

        cols, rows, _ = self.data.shape
        common_valid_indices = np.full((rows, cols), True, dtype=bool)
        
        for key in key_list:
            if "meta_data" in self.global_dict:
                if key in self.global_dict["meta_data"]:
                    continue
            if key not in self.metadata_dict:
                common_valid_indices = np.full((rows, cols), False, dtype=bool)
                break
            array = self.metadata_dict[key]["data"]
            if "missing_value" not in self.metadata_dict[key]:
                continue
            missing_value = self.metadata_dict[key]["missing_value"]
            valid_indices = (array != missing_value)
            common_valid_indices &= valid_indices
        
        # Get valid xy pairs based on common valid indices
        for idx in np.argwhere(common_valid_indices):
            xy_pair = tuple(idx)
            valid_xy_pairs.append(xy_pair)

        for x, y in valid_xy_pairs:
            if criteria.check(self, str(x), str(y)):
                x_coords.append(x)
                y_coords.append(y)
                return_pairs.append((x, y))

        if len(return_pairs) == 0:
            return [], (None, None)
            
        # Calculate the centroid based on the extents of x and y coordinates
        if calculate_centroid:
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            centroid_x = (min_x + max_x) / 2
            centroid_y = (min_y + max_y) / 2
        else:
            centroid_x = None
            centroid_y = None
            
        return valid_xy_pairs, (centroid_x, centroid_y)
        
    def get_spectrum(self, x: Union[int, float] = None, y: Union[int, float] = None) -> Optional[np.ndarray]:
        if (x is None) or (y is None):
            return None
        x = int(x)
        y = int(y)
        return self.data[y, x, :]
        
    def get_meta_data(self, x=None, y=None, key: str = "type"):
        if key == "x":
            return x
        elif key == "y":
            return y

        if key in self.metadata_dict:
            if x is None and y is None:
                return self.metadata_dict[key]["data"]
            else:
                return self.metadata_dict[key]["data"][int(y),int(x),0]
            
        if "meta_data" in self.global_dict and key in self.global_dict["meta_data"]:
            return self.global_dict["meta_data"][key]

        return None

    """
    def get_meta_global_data(self, key):
        if key in self.global_dict:
            return(self.global_dict[key])
        elif key in self.global_dict["meta_data"]:
            return(self.global_dict["meta_data"][key])
            
        if "default" in self.global_dict:
            if key in self.global_dict["default"]:
                return self.global_dict["default"][key]
        
        return(None)
    """        
    def get_wavelengths(self) -> List:
        if self.wavenumbers is None:
            arr = self.get_spectrum(0, 0)  # get a pixel
            self.wavenumbers = np.arange(arr.size)

        return self.wavenumbers
            
    def get_numpy_xy(self):
        return np.transpose(self.data, (1, 0, 2))
    
    def get_numpy_yx(self):
        return self.data
    
    """
    def get_all_xy_pairs(self, include_background=False):
        all_pixel_coords = [(int(x_str), int(y_str)) for x_str, column_dict in self.pixel_dict.items()
                for y_str, meta_dict in column_dict.items()]
        return (all_pixel_coords)

    def get_all_x_values(self, include_background=False):
        return (list(self.pixel_dict.keys()))
        
    def get_y_values_at(self, x, include_background=False):
        y_values = list(self.pixel_dict[x].keys())
        return(y_values)
    """
    def get_all_xy_pairs(self, include_background: bool = False) -> List[Tuple]:
        all_pixel_coords = [(x, y) for x in range(self.width) for y in range(self.height)]
        return all_pixel_coords

    def get_all_x_values(self, include_background: bool = False) -> List[str]:
        all_x_values = [str(x) for x in range(self.width)]
        return all_x_values

    def get_y_values_at(self, x, include_background: bool = False) -> List[str]:
        all_y_values = [str(y) for y in range(self.height)]
        return all_y_values
        
    def add_preprocessing_note(self, note_dic: Dict):
        if self.global_dict is None:
            self.global_dict = {}
            
        if "preprocessing" not in self.global_dict:
            self.global_dict["preprocessing"] = []
            
        self.global_dict["preprocessing"].append(note_dic)

    @staticmethod
    def create_envi_image(data: np.ndarray, wavelengths: List) -> SpyFile:
        lines, samples, bands = data.shape

        # Define the metadata for the ENVI image
        pixel_dict = {
            'description': 'ENVI Image',
            'lines': lines,
            'samples': samples,
            'bands': bands,
            'data type': 4,        # 4 represents 32-bit float
            'interleave': 'bsq',   # 'bsq' means band sequential
            'wavelength': wavelengths
        }

        # Create the ENVI image from the NumPy array and metadata
        envi_image = envi.create_image('', data, metadata=pixel_dict)

        return envi_image

    def copy(self, sample_id: str = None, region_id: str = None, data: np.ndarray = None,
             global_dict: Dict = None, metadata_dict: Dict = None, wavenumbers: List = None) -> 'HappyData':
        """
        Returns a new HappyData instance, filling in any None parameters with copies of its own values.

        :param sample_id: the new sample ID
        :type sample_id: str
        :param region_id: the new region ID
        :type region_id: str
        :param data: the new data
        :type data: np.ndarray
        :param global_dict: the global meta-data
        :type global_dict: dict
        :param metadata_dict: the meta-data
        :type metadata_dict: dict
        :param wavenumbers: the wave numbers
        :type wavenumbers: list
        :return: the new HappyData instance
        :rtype: HappyData
        """
        if sample_id is None:
            sample_id = self.sample_id
        if region_id is None:
            region_id = self.region_id
        if data is None:
            data = self.data.copy()
        if global_dict is None:
            global_dict = copy.deepcopy(self.global_dict)
        if metadata_dict is None:
            metadata_dict = copy.deepcopy(self.metadata_dict)
        if wavenumbers is None:
            if self.wavenumbers is not None:
                wavenumbers = copy.deepcopy(self.wavenumbers)
        return HappyData(sample_id, region_id, data, global_dict, metadata_dict, wavenumbers=wavenumbers)
