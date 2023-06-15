from happy.core import ConfigurableObject, get_func, get_funcname
from happy.readers.json_reader import JsonReader


class SpectraReader(ConfigurableObject):

    def __init__(self, base_dir=None, json_dir=None, filename_func=None):
        self.base_dir = base_dir
        self.filename_func = filename_func
        self.data = None
        self.json_dir = json_dir
        self.json_reader = None
        self.sample_id=None
        self.width = None
        self.height = None
        
    def to_dict(self):
        d = super().to_dict()
        d['base_dir'] = self.base_dir
        d['json_dir'] = self.json_dir
        if self.filename_func is not None:
            d['filename_func'] = self.filename_func.__module__ + "." + self.filename_func.__name__
        return d

    def from_dict(self, d):
        super().from_dict(d)
        self.base_dir = d['base_dir']
        self.json_dir = d['json_dir']
        self.filename_func = None
        if "filename_func" in d:
            self.filename_func = get_func(d["filename_func"])

    def load_data(self, sample_id):
        self.sample_id = sample_id
        self.load_jsons(sample_id)

    def get_spectrum(self, x, y):
        raise NotImplementedError
        
    def get_numpy(self, x, y):
        raise NotImplementedError
    
    def get_wavelengths(self):
        raise NotImplementedError
        
    def load_jsons(self, sample_id):
        # Load the global json
        self.json_reader = JsonReader(self.json_dir, sample_id)
        self.json_reader.load_pixel_json()
        self.json_reader.load_global_json()
