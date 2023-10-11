import argparse
from ._pixel_selector import PixelSelector
from happy.base.core import ConfigurableObject


class MultiSelector(PixelSelector):

    def __init__(self, selectors=None):
        self.selectors = selectors
        self.n = 0
        self._calc_n()

    def name(self) -> str:
        return "multi-ps"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-s", "--selectors", type=str, help="TODO", required=False, nargs="*")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.selectors = []
        if (ns.selectors is not None) and (len(ns.selectors) > 0):
            self.selectors = [ConfigurableObject.from_json(selector) for selector in ns.selectors]
        self._calc_n()

    def _calc_n(self):
        if self.selectors is not None:
            self.n = sum(obj.n for obj in self.selectors)
        else:
            self.n = 0

    def get_n(self):
        return self.n

    def to_dict(self):
        data = super().to_dict()
        data['selectors'] = [selector.to_dict() for selector in self.selectors]
        return data

    def from_dict(self, d):
        super().from_dict(d)
        self.selectors = [ConfigurableObject.create_from_dict(sub) for sub in d["selectors"]]
        self._calc_n()
        return self

    def select_pixels(self, happy_data, n=None):
        pixels = []
        for selector in self.selectors:
            more_pixels = selector.select_pixels(happy_data, n=n)
            pixels.extend(more_pixels)
        return pixels
