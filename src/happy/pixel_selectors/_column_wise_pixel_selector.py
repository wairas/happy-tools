import argparse
import random
import numpy as np

from typing import Union, Dict, Optional

from happy.criteria import Criteria, CriteriaGroup
from happy.data import HappyData
from ._base_pixel_selector import BasePixelSelector


class ColumnWisePixelSelector(BasePixelSelector):

    def __init__(self, n: int = 0, c: int = 0, seed: int = None, criteria: Optional[Union[Criteria, CriteriaGroup]] = None):
        super().__init__(n, criteria)
        self.c = c
        self.seed = seed
        self.rng = None

    def name(self) -> str:
        return "ps-column-wise"

    def description(self) -> str:
        return "Calculates the average of randomly selected pixels per column."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-C", "--column", type=int, help="The column to select pixels from (0-based index).", required=False, default=0)
        parser.add_argument("-S", "--seed", type=int, help="The seed to use for reproducible results", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.c = ns.column
        self.seed = ns.seed
        self.rng = None

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data['c'] = self.c
        data['seed'] = self.seed
        return data

    def from_dict(self, d: Dict):
        super().from_dict(d)
        self.c = d["c"]
        self.seed = d["seed"]
        self.rng = None
        return self

    def get_at(self, happy_data: HappyData, x: int, y: int) -> Optional[Union[int, float]]:
        # Get the pixel data at the specified location (x, y) from the happy_data
        # Find some random pixels in the column and average them
        if x is None:
            self.logger().warning("x is None!")
        column_pixels = []
        all_ys = list(range(happy_data.height))
        if self.rng is None:
            self.rng = random.Random(self.seed)
        self.rng.shuffle(all_ys)
        enough = False
        for num in all_ys:
            if self.criteria.check(happy_data, x, num):
                column_pixels.append(happy_data.get_spectrum(x, num))
            if len(column_pixels) == self.c:
                enough = True
                break
        if not enough:
            return None
        pixel_value = np.mean(column_pixels, axis=0)
        return pixel_value
