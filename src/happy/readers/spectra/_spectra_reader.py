class SpectraReader:
    def __init__(self, base_dir, filename_func):
        self.base_dir = base_dir
        self.filename_func = filename_func
        self.data = None
        self.sample_id=None
        self.width = None
        self.height = None
        
    def to_dict(self):
        return{
            'class': self.__class__.__name__,
            'base_dir': self.base_dir,
        }

    def load_data(self, sample_id):
        self.sample_id = sample_id

    def get_spectrum(self, x, y):
        raise NotImplementedError
        
    def get_numpy(self):
        raise NotImplementedError

    def get_wavelengths(self):
        raise NotImplementedError
