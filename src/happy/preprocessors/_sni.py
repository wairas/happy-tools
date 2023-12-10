import argparse
import numpy as np

from ._preprocessor import Preprocessor


class SpectralNoiseInterpolator(Preprocessor):

    def name(self) -> str:
        return "sni"

    def description(self) -> str:
        return "Spectral noise interpolation"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-t", "--threshold", type=float, help="TODO", required=False, default=0.8)
        # TODO not used?
        #parser.add_argument("-n", "--neighborhood_size", type=int, help="TODO", required=False, default=2)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params['threshold'] = ns.threshold
        # TODO not used?
        #self.params['neighborhood_size'] = ns.neighborhood_size

    def calculate_gradient(self, data):
        # Calculate the gradient along the spectral dimension
        spectral_gradient = np.gradient(data, axis=2)
        self.logger().info(f"data:{data.shape} grad:{spectral_gradient.shape}")
        return spectral_gradient

    def identify_noisy_pixels(self, gradient_data):
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=(0, 1), keepdims=True))
        #gradient_diff = np.abs(gradient_data - np.mean(gradient_data, axis=2, keepdims=True))
        gradient_diff = np.abs(gradient_data - np.median(gradient_data, axis=(0, 1), keepdims=True))
        noisy_pixel_indices = gradient_diff > self.params.get('threshold', 0.8)
        return noisy_pixel_indices

    def interpolate_noisy_pixels(self, data, noisy_pixel_indices, gradient_data):
        interpolated_data = data.copy()
        num_wavelengths = data.shape[2]

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

    def _do_apply(self, data, metadata=None):
        gradient_data = self.calculate_gradient(data)
        noisy_pixel_indices = self.identify_noisy_pixels(gradient_data)
        interpolated_data = self.interpolate_noisy_pixels(data, noisy_pixel_indices, gradient_data)
        return interpolated_data, metadata
