import argparse
import numpy as np

from ._preprocessor import Preprocessor


class CropPreprocessor(Preprocessor):

    def name(self) -> str:
        return "crop"

    def description(self) -> str:
        return "Crops the data to the specified rectangle."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-x", "--x", type=int, help="The left of the cropping rectangle", required=False, default=0)
        parser.add_argument("-y", "--y", type=int, help="The top of the cropping rectangle", required=False, default=0)
        parser.add_argument("-W", "--width", type=int, help="The width of the cropping rectangle", required=False, default=0)
        parser.add_argument("-H", "--height", type=int, help="The height of the cropping rectangle", required=False, default=0)
        parser.add_argument("-p", "--pad", action="store_true", help="Whether to pad if necessary", required=False)
        parser.add_argument("-v", "--pad_value", type=int, help="The value to pad with", required=False, default=0)
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
        # print(f"Padding array with pad_height: {pad_height}, pad_width: {pad_width}")
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
        self.logger().info(data.shape)
        # cropped_data = data[y:y + height, x:x + width, :]
        cropped_data = data[y:y + height, x:x + width, :]
        self.logger().info(f"y: {y}")
        self.logger().info(f"height: {height}")
        self.logger().info(f"cropped_data.shape: {cropped_data.shape}")
        if pad:
            self.logger().info("do pad")
            cropped_data = self.pad_array(cropped_data, height, width, pad_value)
        self.logger().info(f"padded: {cropped_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(metadata, x, y, width, height, pad, pad_value)

        if (new_meta_data is not None) and ("mask" in new_meta_data) and ("data" in new_meta_data["mask"]):
            self.logger().info("pp shape")
            self.logger().info(new_meta_data["mask"]["data"].shape)

        return cropped_data, new_meta_data
