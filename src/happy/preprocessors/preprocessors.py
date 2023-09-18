from sklearn.decomposition import PCA
from happy.preprocessors.preprocessor import Preprocessor
from sklearn.preprocessing import StandardScaler
import spectral.io.envi as envi
import numpy as np
from scipy.signal import savgol_filter


class SpectralNoiseInterpolator(Preprocessor):
    def __init__(self, threshold=0.8, neighborhood_size=2, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold
        self.neighborhood_size = neighborhood_size

    def calculate_gradient(self, data):
        # Calculate the gradient along the spectral dimension
        spectral_gradient = np.gradient(data, axis=2)
        #print(f"data:{data.shape} grad:{spectral_gradient.shape}")
        return spectral_gradient

    def identify_noisy_pixels(self, gradient_data):
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=(0, 1), keepdims=True))
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=2, keepdims=True))
        gradient_diff = np.abs(gradient_data - np.median(gradient_data, axis=(0, 1), keepdims=True))
        noisy_pixel_indices = gradient_diff > self.threshold
        return noisy_pixel_indices

    def interpolate_noisy_pixels(self, data, noisy_pixel_indices, gradient_data):
        interpolated_data = data.copy()
        num_wavelengths = data.shape[2]

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                for k in range(data.shape[2]-1):
                    if noisy_pixel_indices[i, j, k]:
                        # Calculate indices for surrounding pixels
                        surrounding_pixels = np.array([
                            (i-1, j), (i+1, j), (i, j-1), (i, j+1)
                        ])

                        # Clip indices to valid range
                        surrounding_pixels = np.clip(surrounding_pixels, 0, [data.shape[0] - 1, data.shape[1] - 1])

                        # Extract the gradient values at surrounding pixels for the next wavelength (k+1)
                        surrounding_gradients = gradient_data[surrounding_pixels[:, 0], surrounding_pixels[:, 1], k + 1]

                        # Interpolate by averaging surrounding gradient values
                        interpolated_gradient = np.mean(surrounding_gradients)
                        interpolated_data[i, j, k + 1] = data[i, j, k] + interpolated_gradient

        return interpolated_data

    def apply(self, data, metadata=None):
        gradient_data = self.calculate_gradient(data)
        noisy_pixel_indices = self.identify_noisy_pixels(gradient_data)
        interpolated_data = self.interpolate_noisy_pixels(data, noisy_pixel_indices, gradient_data)
        return interpolated_data, metadata

    def to_string(self):
        class_name = self.__class__.__name__
        arguments = ", ".join(f"{key}={value}" for key, value in self.params.items())
        return f"{class_name}({arguments})"


def check_ragged_data(data):
    first_shape = data[0].shape
    for i, array in enumerate(data):
        if array.shape != first_shape:
            print("Data contains arrays with different shapes.")
            print("Shape of the first array:", first_shape)
            print("Index:", i, "Shape:", array.shape)
            return False
    print("Data is consistent. All arrays have the same shape:", first_shape)
    return True


def remove_ragged_data(data, do_print_shapes=True):
    if do_print_shapes:
        print("Before removing ragged data:")
        print_shape(data)

    first_shape = data[0].shape
    consistent_data = [arr for arr in data if arr.shape[0] == first_shape[0]]

    if do_print_shapes:
        print("\nAfter removing ragged data:")
        print_shape(consistent_data)

    return np.array(consistent_data)


def print_shape(data):
    print(data.shape)


class PassThrough(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Call the base class constructor to handle kwargs
        # Initialize any additional instance variables here
        
    def apply(self, data, metadata=None):
        # Apply Standard Normal Variate (SNV) correction along the wavelength dimension
        return data, metadata


class SNVPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Call the base class constructor to handle kwargs
        # Initialize any additional instance variables here
        
    def apply(self, data, metadata=None):
        #is_ragged = check_ragged_data(data)
        mean = np.mean(data, axis=2, keepdims=True)
        std = np.std(data, axis=2, keepdims=True)
        normalized_data = (data - mean) / std
        return normalized_data, metadata


class PCAPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n_components  = self.params.get('components', 5)
        self.percent_pixels  = self.params.get('percent_pixels', 100)
        self.pca = None

    def fit(self, data, metadata=None):
        num_pixels = data.shape[0] * data.shape[1]
        num_samples = int(num_pixels * (self.percent_pixels/100))
        # Flatten the data for dimensionality reduction
        flattened_data = np.reshape(data, (num_pixels, data.shape[2]))
        # Randomly sample pixels
        sampled_indices = np.random.choice(num_pixels, num_samples, replace=False)
        sampled_data = flattened_data[sampled_indices]

        # Perform PCA fit on the sampled data
        self.pca = PCA(n_components=self.n_components)
        self.pca.fit(sampled_data)

        return self

    def apply(self, data, metadata=None):
        if self.pca is None:
            raise ValueError("PCA model has not been fitted. Call the 'fit' method first.")

        num_pixels = data.shape[0] * data.shape[1]
        
        flattened_data = np.reshape(data, (num_pixels, data.shape[2]))
        
        ## Randomly sample pixels
        #sampled_indices = np.random.choice(num_pixels, num_samples, replace=False)
        #sampled_data = flattened_data[sampled_indices]
        
        ## Flatten the data for dimensionality reduction
        #flattened_data = np.reshape(data, (data.shape[0] * data.shape[1], data.shape[2]))

        # Apply PCA transformation to reduce dimensionality
        reduced_data = self.pca.transform(flattened_data)

        # Reshape the reduced data back to its original shape
        processed_data = np.reshape(reduced_data, (data.shape[0], data.shape[1], self.pca.n_components_))

        return processed_data, metadata


class WhiteReferencePreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def apply(self, data, metadata=None):
        white_reference = self.params.get('white_reference', None)
        if white_reference is None:
            white_reference_file = self.params.get('white_reference_file', None)
            filename = self.filename_func(self.base_dir, self.sample_id)
            open = envi.open(filename)
            white_reference = open.load()
        if white_reference is not None:
            # Apply white reference correction by dividing the data by the provided white reference
            corrected_data = data / white_reference
            return corrected_data, metadata
        else:
            return data, metadata


class BlackReferencePreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def apply(self, data, metadata=None):
        black_reference = self.params.get('black_reference', None)
        if black_reference is None:
            black_reference_file = self.params.get('black_reference_file', None)
        if black_reference_file is not None:          
            open = envi.open(black_reference_file)
            black_reference = open.load()
            
        if black_reference is not None:
            # Apply black reference correction by subtracting the provided black reference from the data
            corrected_data = data - black_reference
            return corrected_data, metadata
        else:
            return data, metadata


class DerivativePreprocessor(Preprocessor):
    def apply(self, data, metadata=None, **kwargs):
        window_length = self.params.get('window_length', 5)
        polyorder = self.params.get('polyorder', 2)
        deriv = self.params.get('deriv', 1)
        
        # Apply Savitzky-Golay derivative along the wavelength dimension
        derivative_data = savgol_filter(data, window_length, polyorder, deriv=deriv, axis=2)
        return derivative_data, metadata

class DownsamplePreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def update_pixel_data(self, meta_dict, xth, yth):
        if meta_dict is None:
            return None

        #for key in meta_dict.items():
        #    meta_dict["key"]["data"] = meta_dict["key"]["data"][:, ::xth, :]
            
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = sub_dict["data"][::yth, ::xth]
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict
        
        return new_dict
        
    def apply(self, data, metadata=None):
        xth = self.params.get('xth', 2)
        yth = self.params.get('yth', 2)
        downsampled_data = data[:, ::xth, :]
        downsampled_data = downsampled_data[::yth, :, :]
        new_meta_data = self.update_pixel_data(metadata, xth, yth)
        return downsampled_data, new_meta_data


class PadPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def pad_array(self, array, target_height, target_width, pad_value=0):
        current_height, current_width = array.shape[:2]

        if current_height >= target_height and current_width >= target_width:
            # Array is already larger than or equal to the target size, return as is
            #print(f"Current dimensions: {current_height}x{current_width}, Target dimensions: {target_height}x{target_width}")
            #print("No padding needed.")
            return array

        # Calculate the padding amounts
        pad_height = max(target_height - current_height, 0)
        pad_width = max(target_width - current_width, 0)

        # Calculate padding for each dimension
        padding = [(0, pad_height), (0, pad_width)]
        for _ in range(array.ndim - 2):
            padding.append((0, 0))

        # Create a new array with the desired target size
        #print(f"Padding array with pad_height: {pad_height}, pad_width: {pad_width}")
        padded_array = np.pad(array, padding, mode='constant', constant_values=pad_value)

        return padded_array

    def update_pixel_data(self, meta_dict, width, height, pad_value):
        if meta_dict is None:
            return None

        """    
        new_meta = {}
        for key, value in meta_dict.items():
            #print(key)
            meta_dict[key]["data"] = meta_dict[key]["data"][y:y + height, x:x + width]
        """    
        new_dict = {}
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = self.pad_array(meta_dict[key]["data"], height, width, pad_value)
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict
        
        return new_dict
        
    def apply(self, data, metadata=None):
        # Crop the numpy array
        
        height = self.params.get('height', 0)
        width = self.params.get('width', 0)
        pad_value = self.params.get('pad_value', 0)
        #print(data.shape)
        
        pad_data = self.pad_array(data, height, width, pad_value)
        #print(f"padded:{pad_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(metadata, width, height, pad_value)
        
        #print("pp shape")
        #print(new_meta_data["mask"]["data"].shape)

        return pad_data, new_meta_data


class CropPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def pad_array(self, array, target_height, target_width, pad_value=0):
        current_height, current_width = array.shape[:2]

        if current_height >= target_height and current_width >= target_width:
            # Array is already larger than or equal to the target size, return as is
            #print(f"Current dimensions: {current_height}x{current_width}, Target dimensions: {target_height}x{target_width}")
            #print("No padding needed.")
            return array

        # Calculate the padding amounts
        pad_height = max(target_height - current_height, 0)
        pad_width = max(target_width - current_width, 0)

        # Calculate padding for each dimension
        padding = [(0, pad_height), (0, pad_width)]
        for _ in range(array.ndim - 2):
            padding.append((0, 0))

        # Create a new array with the desired target size
        #print(f"Padding array with pad_height: {pad_height}, pad_width: {pad_width}")
        padded_array = np.pad(array, padding, mode='constant', constant_values=pad_value)

        return padded_array

        
    def update_pixel_data(self, meta_dict, x, y, width, height, pad, pad_value):
        if meta_dict is None:
            return None

        """    
        new_meta = {}
        for key, value in meta_dict.items():
            #print(key)
            meta_dict[key]["data"] = meta_dict[key]["data"][y:y + height, x:x + width]
        """    
        new_dict = {}
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = sub_dict["data"][y:y + height, x:x + width]
                if pad:
                    new_data = self.pad_array(new_data, height, width, pad_value)
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict
        
        return new_dict
        
    def apply(self, data, metadata=None):
        # Crop the numpy array
        x = self.params.get('x', 0)
        y = self.params.get('y', 0)
        height = self.params.get('height', 0)
        width = self.params.get('width', 0)
        pad = self.params.get('pad', True)
        pad_value = self.params.get('pad_value', 0)
        #print(data.shape)
        #cropped_data = data[y:y + height, x:x + width, :]
        cropped_data = data[y:y + height, x:x + width, :]
        #print(y)
        #print(height)
        #print(cropped_data.shape)
        if pad:
            #print("do pad")
            cropped_data = self.pad_array(cropped_data, height, width, pad_value)
        #print(f"padded:{cropped_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(metadata, x, y, width, height, pad, pad_value)
        
        #print("pp shape")
        #print(new_meta_data["mask"]["data"].shape)

        return cropped_data, new_meta_data


class StandardScalerPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Call the base class constructor to handle kwargs
        
    def apply(self, data, metadata=None):
        scaler = StandardScaler()
        reshaped_data = data.reshape(-1, data.shape[-1])  # Flatten the data along the last dimension
        scaled_data = scaler.fit_transform(reshaped_data)
        scaled_data = scaled_data.reshape(data.shape)  # Reshape back to the original shape
        return scaled_data, metadata


class WavelengthSubsetPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def apply(self, data, metadata=None):
        subset_indices = self.params.get('subset_indices', None)
        if subset_indices is not None:
            # Select the subset of wavelengths from the data
            subset_data = data[:, :, subset_indices]
            return subset_data, metadata
        else:
            return data, metadata


class MultiPreprocessor(Preprocessor):
    def __init__(self, **kwargs):#, preprocessor_list=preprocessor_list):
        super().__init__(**kwargs)  # Call the base class constructor to handle kwargs

        self.preprocessor_list = self.params.get('preprocessor_list', [])

    def fit(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            preprocessor.fit(data, metadata)
            data, metadata = preprocessor.apply(data, metadata)
        return self

    def apply(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            data, metadata = preprocessor.apply(data, metadata)
        return data, metadata

    def to_string(self):
        preprocessor_strings = [preprocessor.to_string() for preprocessor in self.preprocessor_list]
        return " -> ".join(preprocessor_strings)
