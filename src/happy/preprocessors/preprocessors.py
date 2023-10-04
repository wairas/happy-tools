import argparse
import copy
from sklearn.decomposition import PCA
from happy.base.registry import REGISTRY
from happy.preprocessors.preprocessor import Preprocessor
from sklearn.preprocessing import StandardScaler
import spectral.io.envi as envi
import numpy as np
from scipy.signal import savgol_filter
from seppl import split_cmdline, split_args


class SpectralNoiseInterpolator(Preprocessor):

    def name(self) -> str:
        return "sni"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-t", "--threshold", type=float, help="TODO", required=False, default=0.8)
        # TODO not used?
        #parser.add_argument("-n", "--neighborhood_size", type=int, help="TODO", required=False, default=2)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params['threshold'] = ns.threshold
        # TODO not used?
        #self.params['neighborhood_size'] = ns.neighborhood_size

    def calculate_gradient(self, data):
        # Calculate the gradient along the spectral dimension
        spectral_gradient = np.gradient(data, axis=2)
        #print(f"data:{data.shape} grad:{spectral_gradient.shape}")
        return spectral_gradient

    def identify_noisy_pixels(self, gradient_data):
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=(0, 1), keepdims=True))
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=2, keepdims=True))
        gradient_diff = np.abs(gradient_data - np.median(gradient_data, axis=(0, 1), keepdims=True))
        noisy_pixel_indices = gradient_diff > self.params.get('threshold', 0.8)
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

    def _do_apply(self, data, metadata=None):
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

    def name(self) -> str:
        return "pass-through"

    def description(self) -> str:
        return "Dummy, just passes through the data"

    def _do_apply(self, data, metadata=None):
        # Apply Standard Normal Variate (SNV) correction along the wavelength dimension
        return data, metadata


class SNVPreprocessor(Preprocessor):

    def name(self) -> str:
        return "snv"

    def description(self) -> str:
        return "TODO"

    def _do_apply(self, data, metadata=None):
        #is_ragged = check_ragged_data(data)
        mean = np.mean(data, axis=2, keepdims=True)
        std = np.std(data, axis=2, keepdims=True)
        normalized_data = (data - mean) / std
        return normalized_data, metadata


class PCAPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pca"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-n", "--components", type=int, help="TODO", required=False, default=5)
        parser.add_argument("-p", "--percent_pixels", type=float, help="TODO", required=False, default=100.0)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["components"] = ns.components
        self.params["percent_pixels"] = ns.percent_pixels

    def _initialize(self):
        super()._initialize()
        self.pca = None

    def _do_fit(self, data, metadata=None):
        num_pixels = data.shape[0] * data.shape[1]
        num_samples = int(num_pixels * (self.params.get('percent_pixels', 100)/100))
        # Flatten the data for dimensionality reduction
        flattened_data = np.reshape(data, (num_pixels, data.shape[2]))
        # Randomly sample pixels
        sampled_indices = np.random.choice(num_pixels, num_samples, replace=False)
        sampled_data = flattened_data[sampled_indices]

        # Perform PCA fit on the sampled data
        self.pca = PCA(n_components=self.params.get('components', 5))
        self.pca.fit(sampled_data)

        return self

    def _do_apply(self, data, metadata=None):
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

    def name(self) -> str:
        return "white-ref"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-f", "--white_reference_file", type=str, help="TODO", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["white_reference_file"] = ns.white_reference_file

    def _do_apply(self, data, metadata=None):
        white_reference = self.params.get('white_reference', None)
        white_reference_file = None
        if white_reference is None:
            white_reference_file = self.params.get('white_reference_file', None)
        if white_reference_file is not None:
            ref = envi.open(white_reference_file)
            white_reference = ref.load()
        if white_reference is not None:
            # Apply white reference correction by dividing the data by the provided white reference
            corrected_data = data / white_reference
            return corrected_data, metadata
        else:
            return data, metadata


class BlackReferencePreprocessor(Preprocessor):

    def name(self) -> str:
        return "black-ref"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-f", "--black_reference_file", type=str, help="TODO", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["black_reference_file"] = ns.black_reference_file

    def _do_apply(self, data, metadata=None):
        black_reference = self.params.get('black_reference', None)
        black_reference_file = None
        if black_reference is None:
            black_reference_file = self.params.get('black_reference_file', None)
        if black_reference_file is not None:          
            ref = envi.open(black_reference_file)
            black_reference = ref.load()
        if black_reference is not None:
            # Apply black reference correction by subtracting the provided black reference from the data
            corrected_data = data - black_reference
            return corrected_data, metadata
        else:
            return data, metadata


class DerivativePreprocessor(Preprocessor):

    def name(self) -> str:
        return "derivative"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-w", "--window_length", type=int, help="TODO", required=False, default=5)
        parser.add_argument("-p", "--polyorder", type=int, help="TODO", required=False, default=2)
        parser.add_argument("-d", "--deriv", type=int, help="TODO", required=False, default=1)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["window_length"] = ns.window_length
        self.params["polyorder"] = ns.polyorder
        self.params["deriv"] = ns.deriv

    def _do_apply(self, data, metadata=None):
        window_length = self.params.get('window_length', 5)
        polyorder = self.params.get('polyorder', 2)
        deriv = self.params.get('deriv', 1)
        
        # Apply Savitzky-Golay derivative along the wavelength dimension
        derivative_data = savgol_filter(data, window_length, polyorder, deriv=deriv, axis=2)
        return derivative_data, metadata


class DownsamplePreprocessor(Preprocessor):

    def name(self) -> str:
        return "down-sample"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-x", "--xth", type=int, help="TODO", required=False, default=2)
        parser.add_argument("-y", "--yth", type=int, help="TODO", required=False, default=2)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["xth"] = ns.xth
        self.params["yth"] = ns.yth

    def update_pixel_data(self, meta_dict, xth, yth):
        if meta_dict is None:
            return None

        #for key in meta_dict.items():
        #    meta_dict["key"]["data"] = meta_dict["key"]["data"][:, ::xth, :]
            
        new_dict = {}
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = sub_dict["data"][::yth, ::xth]
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict
        
        return new_dict
        
    def _do_apply(self, data, metadata=None):
        xth = self.params.get('xth', 2)
        yth = self.params.get('yth', 2)
        downsampled_data = data[:, ::xth, :]
        downsampled_data = downsampled_data[::yth, :, :]
        new_meta_data = self.update_pixel_data(metadata, xth, yth)
        return downsampled_data, new_meta_data


class PadPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pad"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-W", "--width", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-H", "--height", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-v", "--pad_value", type=int, help="TODO", required=False, default=0)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["width"] = ns.width
        self.params["height"] = ns.height
        self.params["pad_value"] = ns.pad_value

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
        
    def _do_apply(self, data, metadata=None):
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

    def name(self) -> str:
        return "crop"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-x", "--x", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-y", "--y", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-W", "--width", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-H", "--height", type=int, help="TODO", required=False, default=0)
        parser.add_argument("-p", "--pad", action="store_true", help="TODO", required=False)
        parser.add_argument("-v", "--pad_value", type=int, help="TODO", required=False, default=0)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["x"] = ns.x
        self.params["y"] = ns.y
        self.params["width"] = ns.width
        self.params["height"] = ns.height
        self.params["pad"] = ns.pad
        self.params["pad_value"] = ns.pad_value

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
        
    def _do_apply(self, data, metadata=None):
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

    def name(self) -> str:
        return "std-scaler"

    def description(self) -> str:
        return "TODO"

    def _do_apply(self, data, metadata=None):
        scaler = StandardScaler()
        reshaped_data = data.reshape(-1, data.shape[-1])  # Flatten the data along the last dimension
        scaled_data = scaler.fit_transform(reshaped_data)
        scaled_data = scaled_data.reshape(data.shape)  # Reshape back to the original shape
        return scaled_data, metadata


class WavelengthSubsetPreprocessor(Preprocessor):

    def name(self) -> str:
        return "wavelength-subset"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-s", "--subset_indices", type=int, help="The explicit 0-based wavelength indices to use", required=False, nargs="+")
        parser.add_argument("-f", "--from_index", type=int, help="The first 0-based wavelength to include", required=False, default=60)
        parser.add_argument("-t", "--to_index", type=int, help="The last 0-based wavelength to include", required=False, default=189)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["subset_indices"] = ns.subset_indices
        self.params["from_index"] = ns.from_index
        self.params["to_index"] = ns.to_index

    def _do_apply(self, data, metadata=None):
        subset_indices = self.params.get('subset_indices', None)
        from_index = self.params.get('from_index', None)
        to_index = self.params.get('to_index', None)
        if subset_indices is None:
            if (from_index is not None) and (to_index is not None):
                subset_indices = list(range(from_index, to_index + 1))
        if subset_indices is not None:
            # Select the subset of wavelengths from the data
            subset_data = data[:, :, subset_indices]
            return subset_data, metadata
        else:
            return data, metadata


class MultiPreprocessor(Preprocessor):

    def name(self) -> str:
        return "multi"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-p", "--preprocessors", type=str, help="TODO", required=False, nargs="*")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        preprocessor_list = []
        all = REGISTRY.preprocessors()
        for preprocessor in ns.preprocessors:
            plugins = split_args(split_cmdline(preprocessor), all.keys())
            for key in plugins:
                if key == "":
                    continue
                name = all[key][0]
                plugin = copy.deepcopy(all[name])
                plugin.parse_args(plugins[key][1:])
                preprocessor_list.append(plugin)
        self.params["preprocessor_list"] = preprocessor_list

    def _initialize(self):
        super()._initialize()
        self.preprocessor_list = self.params.get('preprocessor_list', [])

    def _do_fit(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            preprocessor.fit(data, metadata)
            data, metadata = preprocessor.apply(data, metadata)
        return self

    def _do_apply(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            data, metadata = preprocessor.apply(data, metadata)
        return data, metadata

    def to_string(self):
        preprocessor_strings = [preprocessor.to_string() for preprocessor in self.preprocessor_list]
        return " -> ".join(preprocessor_strings)
