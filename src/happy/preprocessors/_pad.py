import argparse
import numpy as np

from typing import Optional, Dict, Tuple

from ._preprocessor import Preprocessor
from ._pad_utils import pad_array


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

    def update_pixel_data(self, meta_dict: Dict, width: int, height: int, pad_value: int) -> Optional[Dict]:
        if meta_dict is None:
            return None

        new_dict = {}
        for key, sub_dict in meta_dict.items():
            if "data" in sub_dict:
                new_data = pad_array(meta_dict[key]["data"], height, width, pad_value, logger=self.logger())
                new_sub_dict = {k: v for k, v in sub_dict.items() if k != "data"}
                new_sub_dict["data"] = new_data
                new_dict[key] = new_sub_dict
            else:
                new_dict[key] = sub_dict

        return new_dict

    def _do_apply(self, data: np.ndarray, metadata: Optional[Dict] = None) -> Tuple[np.ndarray, Optional[Dict]]:
        # Crop the numpy array
        height = self.params.get('height', 0)
        width = self.params.get('width', 0)
        pad_value = self.params.get('pad_value', 0)
        self.logger().info(data.shape)

        pad_data = pad_array(data, height, width, pad_value, logger=self.logger())
        self.logger().info(f"padded:{pad_data.shape}")
        # Update the pixel_data dictionary
        new_meta_data = self.update_pixel_data(metadata, width, height, pad_value)

        if (new_meta_data is not None) and ("mask" in new_meta_data) and ("data" in new_meta_data["mask"]):
            self.logger().info("pp shape")
            self.logger().info(new_meta_data["mask"]["data"].shape)

        return pad_data, new_meta_data
