import argparse
from ._base_pixel_selector import BasePixelSelector
import random
import numpy as np


class ColumnWisePixelSelector(BasePixelSelector):

    def __init__(self, n=0, c=0, criteria=None):
        super().__init__(n, criteria)
        self.c = c

    def name(self) -> str:
        return "column-wise-ps"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-C", "--column", type=int, help="TODO", required=False, default=0)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.c = ns.column

    def to_dict(self):
        data = super().to_dict()
        data['c'] = self.c
        return data

    def from_dict(self, d):
        super().from_dict(d)
        self.c = d["c"]
        return self

    def get_at(self, happy_data, x, y):
        # Get the pixel data at the specified location (x, y) from the happy_data
        # Find some random pixels in the column and average them
        if x is None:
            print("!!NONE")
        column_pixels = []
        all_ys = list(range(happy_data.height))
        random.shuffle(all_ys)
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
