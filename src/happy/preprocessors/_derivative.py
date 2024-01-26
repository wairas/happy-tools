import argparse

from scipy.signal import savgol_filter
from ._preprocessor import Preprocessor
from happy.data import HappyData


class DerivativePreprocessor(Preprocessor):

    def name(self) -> str:
        return "derivative"

    def description(self) -> str:
        return "Applies Savitzky-Golay to the data."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-w", "--window_length", type=int, help="The size of the window (must be odd number)", required=False, default=5)
        parser.add_argument("-p", "--polyorder", type=int, help="The polynominal order", required=False, default=2)
        parser.add_argument("-d", "--deriv", type=int, help="The deriviative to use, 0 is just smoothing", required=False, default=1)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["window_length"] = ns.window_length
        self.params["polyorder"] = ns.polyorder
        self.params["deriv"] = ns.deriv

    def _do_apply(self, happy_data: HappyData) -> HappyData:
        window_length = self.params.get('window_length', 5)
        polyorder = self.params.get('polyorder', 2)
        deriv = self.params.get('deriv', 1)

        # Apply Savitzky-Golay derivative along the wavelength dimension
        derivative_data = savgol_filter(happy_data.data, window_length, polyorder, deriv=deriv, axis=2)
        return happy_data.copy(data=derivative_data)
