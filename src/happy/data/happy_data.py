import spectral.io.envi as envi
import numpy as np
import copy


class HappyData:
    def __init__(self, sample_id, region_id, data, global_dict, metadata_dict, wavenumbers=None):
        self.sample_id = sample_id
        self.region_id = region_id
        self.data = data
        self.global_dict = global_dict
        self.wavenumbers = wavenumbers
        self.width = self.data.shape[1]
        self.height = self.data.shape[0]
        self.metadata_dict = metadata_dict

    def get_full_id(self):
        return(self.sample_id+":"+self.region_id)
        
    def append_region_name(self, to_append):
        self.region_id = self.region_id + "_" + to_append
        
    def get_unique_values(self, target):
        if target not in self.metadata_dict:
            return([])
        data = self.metadata_dict[target]["data"]
        # Assuming 'my_array' is your numpy array
        unique_values = np.unique(data)
        unique_values_list = unique_values.tolist()

        return(unique_values_list)
        
    def apply_preprocess(self, preprocessor_method):
        preprocessor_method.fit(self.data)
        # Apply the specified preprocessing
        preprocessed_data, new_meta_dict = preprocessor_method.apply(self.data, self.metadata_dict)
        

        preprocessed_happy_data = HappyData(self.sample_id, self.region_id, preprocessed_data, copy.deepcopy(self.global_dict), new_meta_dict)
        processing_note = {
            #"source": input_folder,
            "preprocessing" : [preprocessor_method.to_string()]
        }
        preprocessed_happy_data.add_preprocessing_note(processing_note) 
        
        return(preprocessed_happy_data)
        
    """    
    def get_segmentation_labels(self, target, mapping):
        if target in self.metadata_dict:
            return self.metadata_dict[target]["data"], self.metadata_dict[target]["mapping"]
            
        return None, None
    """    
        
    def find_pixels_with_criteria(self, criteria, calculate_centroid=True):
        x_coords = []
        y_coords = []
        valid_xy_pairs  = []
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
                #print(criteria.to_dict())
                
        if len(return_pairs ) == 0:
            return([],(None, None))
            
        # Calculate the centroid based on the extents of x and y coordinates
        if calculate_centroid:
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            centroid_x = (min_x + max_x) / 2
            centroid_y = (min_y + max_y) / 2
        else:
            centroid_x = None
            centroid_y = None
            
        return valid_xy_pairs , (centroid_x, centroid_y)
        
    def get_spectrum(self, x=None, y=None):
        if x is None or y is None:
            return (None)
        x = int(x)
        y = int(y)
        return (self.data[y, x, :])
        
    def get_meta_data(self, x=None, y=None, key="type"):
        if key == "x":
            return(x)
        elif key == "y":
            return(y)
            
        
        if key in self.metadata_dict:
            #print(self.metadata_dict[key]["data"].shape)
            #print (type(self.metadata_dict[key]["data"]))
            if x is None and y is None:
                return(self.metadata_dict[key]["data"])
                #print("return full array")
            else:
                #print(f"return element {self.metadata_dict[key]['data'][int(y),int(x),0]}")
                return self.metadata_dict[key]["data"][int(y),int(x),0]
            
        if "meta_data" in self.global_dict and key in self.global_dict["meta_data"]:
            return self.global_dict["meta_data"][key]
            
       
        return None
        #return(self.get_meta_global_data(key))
        
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
    def get_wavelengths(self):
        if self.wavenumbers is None:
            arr = self.get_spectrum(0,0) # get a pixel
            self.wavenumbers = np.arange(arr.size)
            #print("in here")
            #print(self.wavenumbers)
       
        return(self.wavenumbers)
            
    def get_numpy_xy(self):
        return(np.transpose(self.data, (1, 0, 2)))
    
    def get_numpy_yx(self):
        return(self.data)
    
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
    def get_all_xy_pairs(self, include_background=False):
        
        all_pixel_coords = [(x, y) for x in range(self.width) for y in range(self.height)]
        
        return all_pixel_coords

    def get_all_x_values(self, include_background=False):
        all_x_values = [str(x) for x in range(self.width)]
        
        return all_x_values

    def get_y_values_at(self, x, include_background=False):
        all_y_values = [str(y) for y in range(self.height)]
        
        return all_y_values    
        
    def add_preprocessing_note(self, note_dic):
        if self.global_dict is None:
            self.global_dict = {}
            
        if "preprocessing" not in self.global_dict:
            self.global_dict["preprocessing"] = []
            
        self.global_dict["preprocessing"].append(note_dic)

    @staticmethod
    def create_envi_image(data, wavelengths):
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

