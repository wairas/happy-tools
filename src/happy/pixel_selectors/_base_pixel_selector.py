import abc
import argparse
import random
from happy.base.core import ConfigurableObject
from happy.criteria import Criteria
from ._pixel_selector import PixelSelector


class BasePixelSelector(PixelSelector, abc.ABC):

    def __init__(self, n=0, criteria=None, include_background=False):
        self.n = n
        self.criteria = criteria
        self.include_background = include_background

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-n", type=int, help="The number of pixels", required=True)
        parser.add_argument("-c", "--criteria", type=str, help="The JSON string defining the criteria to apply", required=False, default=None)
        parser.add_argument("-b", "--include_background", action="store_true", help="Whether to include the background", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.n = ns.n
        self.criteria = None
        if ns.criteria is not None:
            self.criteria = Criteria.from_json(ns.criteria)
        self.include_background = ns.include_background

    def get_n(self):
        return self.n
        
    def set_criteria(self, criteria):
        self.criteria = criteria
        
    def check(self, happy_data, x, y):
        if self.criteria is None:
            return True
        else:
            return self.criteria.check(happy_data, x, y)
          
    def to_dict(self):
        result = super().to_dict()
        result["n"] = self.n
        if self.criteria is not None:
            result["criteria"] = self.criteria.to_dict()
        return result

    def from_dict(self, d):
        self.n = d["n"]
        self.criteria = None
        if "criteria" in d:
            self.criteria = ConfigurableObject.create_from_dict(d["criteria"])
        return self

    def get_at(self, happy_data, x, y):
        raise NotImplementedError("Subclasses must implement the get_at method")
    
    def _get_candidate_pixels(self, happy_data):
        # This is a generator function that yields candidate pixels
        # until `n` pixels that match the criteria are found.
        i = 0
        pos = 0
        all_pixel_coords = happy_data.get_all_xy_pairs(self.include_background)
        random.shuffle(all_pixel_coords)
        while i < len(all_pixel_coords) and pos < len(all_pixel_coords):
            x, y = all_pixel_coords[pos]
            pos = pos + 1
            if self.check(happy_data, x, y):
                i += 1
                yield x, y

    def select_pixels(self, happy_data, n=None):
        pixels = []
        if n is None:
            n = self.n

        for x, y in self._get_candidate_pixels(happy_data):
            pixel_value = self.get_at(happy_data, x, y)
            if pixel_value is not None:
                pixels.append((x, y, pixel_value))
            if len(pixels) == n:
                break
        return pixels
