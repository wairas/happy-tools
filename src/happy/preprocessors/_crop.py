import argparse

from typing import Optional, Dict

from ._preprocessor import Preprocessor
from ._pad_utils import pad_array
from happy.data import HappyData


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

    def update_pixel_data(self, meta_dict: Dict, x: int, y: int, width: int, height: int, pad: bool, pad_value: int) -> Optional[Dict]:
        if meta_dict is None:
            return None

        new_dict = {}
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = sub_dict["data"][y:y + height, x:x + width]
                if pad:
                    new_data = pad_array(new_data, height, width, pad_value, logger=self.logger())
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict

        return new_dict

    def _do_apply(self, happy_data: HappyData) -> HappyData:
        # Crop the numpy array
        x = self.params.get('x', 0)
        y = self.params.get('y', 0)
        height = self.params.get('height', 0)
        width = self.params.get('width', 0)
        pad = self.params.get('pad', True)
        pad_value = self.params.get('pad_value', 0)
        self.logger().info(happy_data.data.shape)
        cropped_data = happy_data.data[y:y + height, x:x + width, :]
        self.logger().info(f"y: {y}")
        self.logger().info(f"height: {height}")
        self.logger().info(f"cropped_data.shape: {cropped_data.shape}")
        if pad:
            self.logger().info("do pad")
            cropped_data = pad_array(cropped_data, height, width, pad_value, logger=self.logger())
        self.logger().info(f"padded: {cropped_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(happy_data.metadata_dict, x, y, width, height, pad, pad_value)

        if (new_meta_data is not None) and ("mask" in new_meta_data) and ("data" in new_meta_data["mask"]):
            self.logger().info("pp shape")
            self.logger().info(new_meta_data["mask"]["data"].shape)

        return happy_data.copy(data=cropped_data, metadata_dict=new_meta_data)
