from happy.readers.json_reader import JsonReader


class SpectraReader:
    def __init__(self, base_dir, json_dir, filename_func):
        self.base_dir = base_dir
        self.filename_func = filename_func or self.default_filename_func
        self.data = None
        self.json_dir = json_dir
        self.json_reader = None
        self.sample_id=None
        self.width = None
        self.height = None
        
    def to_dict(self):
        return{
            'class': self.__class__.__name__,
            'base_dir': self.base_dir,
            'json_dir': self.json_dir
        }

    def load_data(self, sample_id):
        self.sample_id = sample_id
        if self.json_dir is not None:
            self.load_jsons(sample_id)

    def get_spectrum(self, x, y):
        raise NotImplementedError
        
    def get_numpy(self, x, y):
        raise NotImplementedError
        
    def default_filename_func(self, sample_id):
        raise NotImplementedError
    
    def get_wavelengths(self):
        raise NotImplementedError
        
    def load_jsons(self, sample_id):
        # Load the global json
        self.json_reader = JsonReader(self.json_dir, sample_id)
        self.json_reader.load_pixel_json()
        self.json_reader.load_global_json()
