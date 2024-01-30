import argparse
import numpy as np

from typing import Optional, Union, List, Dict

from ._base_pixel_selector import BasePixelSelector
from happy.criteria import Criteria, CriteriaGroup
from happy.data import HappyData


class AveragedGridSelector(BasePixelSelector):

    def __init__(self, n: int = 0, grid_size: int = 0, criteria: Optional[Union[Criteria, CriteriaGroup]] = None, include_background: bool = False):
        super().__init__(n, criteria=criteria,include_background=include_background)
        self.grid_size = grid_size

    def name(self) -> str:
        return "ps-grid-wise"

    def description(self) -> str:
        return "Averages the pixels in the defined grid and returns that."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-g", "--grid_size", type=int, help="Width and height of the grid to use", required=False, default=0)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.grid_size = ns.grid_size

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data['grid_size'] = self.grid_size
        return data

    def get_at(self, happy_data: HappyData, x, y):
        # Get the pixel data at the specified location (x, y) from the happy_data
        width, height = happy_data.width, happy_data.height
        x0, x1 = max(0, x - self.grid_size), min(width - 1, x + self.grid_size)
        y0, y1 = max(0, y - self.grid_size), min(height - 1, y + self.grid_size)
        
        results = [self.check(happy_data, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
        if all(results):  # all pass
            z_list = [happy_data.get_spectrum(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
            pixel_value = np.mean(z_list, axis=0)
            return pixel_value
        return None
