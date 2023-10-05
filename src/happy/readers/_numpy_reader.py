import os
import numpy as np
import json
from ._spectra_reader import SpectraReader


class NumpyReader(SpectraReader):
    def __init__(self, base_dir, json_dir, filename_func):
        super().__init__(base_dir, json_dir, filename_func)
        self.wavelengths = None

    def load_data(self, sample_id):
        filename = self.filename_func(self.base_dir, sample_id)
        self.data = np.load(filename)
        self.load_wavelengths(sample_id)
        self.height, self.width, _ = self.data.shape
        super().load_data(sample_id)

    def default_filename_func(self, sample_id):
        return sample_id + '.npy'
        
    def load_wavelengths(self, sample_id):
        filename = self.filename_func(self.json_dir, sample_id)
        json_file = os.path.splitext(filename)[0] + ".json"
        if os.path.exists(json_file):
            with open(json_file) as f:
                json_data = json.load(f)
                self.wavelengths = json_data.get('wavelengths')

    def get_spectrum(self, x, y):
        if self.data is None:
            raise ValueError("Spectral data not loaded. Call load_data() first.")
        return self.data[y, x, :]

    def get_wavelengths(self):
        return self.wavelengths
