import argparse

from typing import Optional, Dict, Tuple

import numpy as np

from ._preprocessor import Preprocessor


class DownsamplePreprocessor(Preprocessor):

    def name(self) -> str:
        return "down-sample"

    def description(self) -> str:
        return "Data reduction preprocessor that takes every x-th pixel on the x-axis and y-th pixel on the y-axis."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-x", "--xth", type=int, help="Every nth pixel on the x axis", required=False, default=2)
        parser.add_argument("-y", "--yth", type=int, help="Every nth pixel on the y axis", required=False, default=2)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["xth"] = ns.xth
        self.params["yth"] = ns.yth

    def update_pixel_data(self, meta_dict: Dict, xth: int, yth: int):
        if meta_dict is None:
            return None

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

    def _do_apply(self, data: np.ndarray, metadata: Optional[Dict] = None) -> Tuple[np.ndarray, Optional[Dict]]:
        xth = self.params.get('xth', 2)
        yth = self.params.get('yth', 2)
        downsampled_data = data[:, ::xth, :]
        downsampled_data = downsampled_data[::yth, :, :]
        new_meta_data = self.update_pixel_data(metadata, xth, yth)
        return downsampled_data, new_meta_data
