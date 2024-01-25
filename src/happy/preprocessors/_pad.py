import argparse
import numpy as np

from ._preprocessor import Preprocessor


class PadPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pad"

    def description(self) -> str:
        return "Pads the data to the specified dimensions with the supplied value"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-W", "--width", type=int, help="The width to pad to", required=False, default=0)
        parser.add_argument("-H", "--height", type=int, help="The height to pad to", required=False, default=0)
        parser.add_argument("-v", "--pad_value", type=int, help="The value to pad with", required=False, default=0)
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
            self.logger().info(f"Current dimensions: {current_height}x{current_width}, Target dimensions: {target_height}x{target_width}")
            self.logger().info("No padding needed.")
            return array

        # Calculate the padding amounts
        pad_height = max(target_height - current_height, 0)
        pad_width = max(target_width - current_width, 0)

        # Calculate padding for each dimension
        padding = [(0, pad_height), (0, pad_width)]
        for _ in range(array.ndim - 2):
            padding.append((0, 0))

        # Create a new array with the desired target size
        self.logger().info(f"Padding array with pad_height: {pad_height}, pad_width: {pad_width}")
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
        self.logger().info(data.shape)

        pad_data = self.pad_array(data, height, width, pad_value)
        self.logger().info(f"padded:{pad_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(metadata, width, height, pad_value)

        if (new_meta_data is not None) and ("mask" in new_meta_data) and ("data" in new_meta_data["mask"]):
            self.logger().info("pp shape")
            self.logger().info(new_meta_data["mask"]["data"].shape)

        return pad_data, new_meta_data
