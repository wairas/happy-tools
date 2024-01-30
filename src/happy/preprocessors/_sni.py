import argparse
import numpy as np

from typing import List

from ._preprocessor import Preprocessor
from happy.data import HappyData


class SpectralNoiseInterpolator(Preprocessor):

    def name(self) -> str:
        return "sni"

    def description(self) -> str:
        return "Spectral noise interpolation. For each pixel it looks at the gradient between "\
               "wavelengths and compares it against the average gradient of surrounding pixels. "\
               "If that difference is larger than the specified threshold (= noisy) then "\
               "interpolate this wavelength."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-t", "--threshold", type=float, help="The threshold for identifying noisy pixels.", required=False, default=0.8)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params['threshold'] = ns.threshold

    def calculate_gradient(self, data: np.ndarray) -> np.ndarray:
        # Calculate the gradient along the spectral dimension
        spectral_gradient = np.gradient(data, axis=2)
        self.logger().info(f"data:{data.shape} grad:{spectral_gradient.shape}")
        return spectral_gradient

    def identify_noisy_pixels(self, gradient_data: np.ndarray) -> np.ndarray:
        gradient_diff = np.abs(gradient_data - np.median(gradient_data, axis=(0, 1), keepdims=True))
        noisy_pixel_indices = gradient_diff > self.params.get('threshold', 0.8)
        return noisy_pixel_indices

    def interpolate_noisy_pixels(self, data: np.ndarray, noisy_pixel_indices: np.ndarray, gradient_data: np.ndarray) -> np.ndarray:
        interpolated_data = data.copy()

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                for k in range(data.shape[2]-1):
                    if noisy_pixel_indices[i, j, k]:
                        # Calculate indices for surrounding pixels
                        surrounding_pixels = np.array([
                            (i-1, j), (i+1, j), (i, j-1), (i, j+1)
                        ])

                        # Clip indices to valid range
                        surrounding_pixels = np.clip(surrounding_pixels, 0, [data.shape[0] - 1, data.shape[1] - 1])

                        # Extract the gradient values at surrounding pixels for the next wavelength (k+1)
                        surrounding_gradients = gradient_data[surrounding_pixels[:, 0], surrounding_pixels[:, 1], k + 1]

                        # Interpolate by averaging surrounding gradient values
                        interpolated_gradient = np.mean(surrounding_gradients)
                        interpolated_data[i, j, k + 1] = data[i, j, k] + interpolated_gradient

        return interpolated_data

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        gradient_data = self.calculate_gradient(happy_data.data)
        noisy_pixel_indices = self.identify_noisy_pixels(gradient_data)
        interpolated_data = self.interpolate_noisy_pixels(happy_data.data, noisy_pixel_indices, gradient_data)
        return [happy_data.copy(data=interpolated_data)]
