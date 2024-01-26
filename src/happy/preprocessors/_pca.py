import argparse
import numpy as np
import pickle

from typing import Optional, Dict, Tuple

from sklearn.decomposition import PCA
from ._preprocessor import Preprocessor


class PCAPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pca"

    def description(self) -> str:
        return "Applies principal components analysis to the data."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-n", "--components", type=int, help="The number of PCA components", required=False, default=5)
        parser.add_argument("-p", "--percent_pixels", type=float, help="The subset of pixels to use (0-100)", required=False, default=100.0)
        parser.add_argument("-l", "--load", type=str, help="The file with the pickled sklearn PCA instance to load and use instead of building one each time data is passing through", required=False, default=None)
        parser.add_argument("-s", "--save", type=str, help="The file to save the fitted sklearn PCA instance to", required=False, default=None)
        parser.add_argument("-S", "--seed", type=int, help="The seed to use for reproducible results", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["components"] = ns.components
        self.params["percent_pixels"] = ns.percent_pixels
        self.params["load"] = ns.load
        self.params["save"] = ns.save
        self.params["seed"] = ns.seed
        self.pca = None

    def _initialize(self):
        super()._initialize()
        percent_pixel = self.params.get('percent_pixels', 100)
        if percent_pixel <= 0:
            raise Exception("'percent_pixels' must be larger than 0, provided: %f" % percent_pixel)
        if percent_pixel > 100:
            raise Exception("'percent_pixels' cannot be larger than 100, provided: %f" % percent_pixel)

    def _do_fit(self, data: np.ndarray, metadata: Optional[Dict] = None):
        if self.params.get('load', None) is not None:
            with open(self.params.get('load', None), "rb") as fp:
                self.pca = pickle.load(fp)
        else:
            num_pixels = data.shape[0] * data.shape[1]
            # Flatten the data for dimensionality reduction
            flattened_data = np.reshape(data, (num_pixels, data.shape[2]))
            # Randomly sample pixels?
            percent = self.params.get('percent_pixels', 100)
            if percent != 100:
                num_samples = int(num_pixels * (self.params.get('percent_pixels', 100) / 100))
                rng = np.random.default_rng(seed=self.params.get('seed', None))
                sampled_indices = rng.choice(num_pixels, num_samples, replace=False)
                sampled_data = flattened_data[sampled_indices]
            else:
                sampled_data = flattened_data

            # Perform PCA fit on the sampled data
            self.pca = PCA(n_components=self.params.get('components', 5), random_state=self.params.get('seed', None))
            self.pca.fit(sampled_data)

            if self.params.get('save', None) is not None:
                with open(self.params.get('save', None), "wb") as fp:
                    pickle.dump(self.pca, fp)

    def _do_apply(self, data: np.ndarray, metadata: Optional[Dict] = None) -> Tuple[np.ndarray, Optional[Dict]]:
        if self.pca is None:
            raise ValueError("PCA model has not been fitted. Call the 'fit' method first.")

        num_pixels = data.shape[0] * data.shape[1]
        flattened_data = np.reshape(data, (num_pixels, data.shape[2]))

        # Apply PCA transformation to reduce dimensionality
        reduced_data = self.pca.transform(flattened_data)

        # Reshape the reduced data back to its original shape
        processed_data = np.reshape(reduced_data, (data.shape[0], data.shape[1], self.pca.n_components_))

        return processed_data, metadata
