from spectra_reader import SpectraReader

class EnviReader(SpectraReader):
    def __init__(self, base_dir, filename_func):
        super().__init__(base_dir, filename_func)

    def load_data(self, sample_id):
        filename = self.filename_func(self.base_dir, sample_id)
        self.data = envi.open(filename).load()
        self.height, self.width, _ = self.data.shape
        super().load_data(sample_id)
        
    def get_spectrum(self, x, y):
        if self.data is None:
            raise ValueError("Spectral data not loaded. Call load_data() first.")
        return self.data[y, x, :]
