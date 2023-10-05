from ._spectra_reader import SpectraReader
import spectral.io.envi as envi
import os
import numpy as np


class EnviReader(SpectraReader):
    def __init__(self, base_dir, json_folder, filename_func=None):
        super().__init__(base_dir, json_folder, filename_func)
        self.wavelengths = None

    def load_data(self, sample_id):
        filename = self.filename_func(self.base_dir, sample_id)
        open = envi.open(filename)
        self.data = open.load()
        self.wavelengths = open.metadata['wavelength']
        if self.wavelengths == 'None':
            self.wavelengths = None
        
        self.height, self.width, _ = self.data.shape
        super().load_data(sample_id)
        
    def get_spectrum(self, x, y):
        if self.data is None:
            raise ValueError("Spectral data not loaded. Call load_data() first.")
        return self.data[y, x, :]

    def get_wavelengths(self):
        return self.wavelengths
        
    def get_numpy_xy(self):
        return np.transpose(self.data, (1, 0, 2))
    
    def get_numpy_yx(self):
        return self.data
        
    def get_numpy(self):
        return np.asarray(self.data)
        
    def default_filename_func(self, base_dir, sample_id):
        return os.path.join(base_dir, sample_id + '.hdr')