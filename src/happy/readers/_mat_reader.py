from happy.readers import SpectraReader
import scipy.io as sio
import argparse
import numpy as np


def default_filename_func(base_dir, sample_id):
    return base_dir + "/" + sample_id + '.mat'


class MatReader(SpectraReader):
    def __init__(self, base_dir, json_dir, filename_func, struct_name, wavelengths_struct=None):
        if filename_func is None:
            filename_func = default_filename_func
        super().__init__(base_dir, json_dir, filename_func)
        self.struct_name = struct_name
        self.wavelengths_struct_name = wavelengths_struct
        self.wavelengths = None
        self.mat_file = None

    def load_data(self, sample_id):
        filename = self.filename_func(self.base_dir, sample_id)
        self.mat_file = sio.loadmat(filename)
        #print("mat loaded")
        self.data = self.mat_file[self.struct_name]
        if self.wavelengths_struct_name:
            self.wavelengths = self.mat_file[self.wavelengths_struct_name]
            #print("shape")
            #print(self.wavelengths.shape)
        if self.wavelengths is None:
            arr = self.get_spectrum(0,0) # get a pixel
            self.wavelengths = np.arange(arr.size)
        self.height, self.width, _ = self.data.shape
        #print("shape")
        #print(self.data.shape)
        #print(self.height)
        #print(self.width)
        super().load_data(sample_id)

    def set_base_dir(self, base_dir):
        self.base_dir = base_dir
        
    def get_numpy(self):
        return self.data
    
    def get_numpy_of(self, sname):
        return self.mat_file[sname]
        
    def get_wavelengths(self):
        return self.wavelengths.flatten()

    def get_spectrum(self, x, y):
        if self.data is None:
            raise ValueError("Spectral data not loaded. Call load_data() first.")
        return self.data[y, x, :]


def main():
    parser = argparse.ArgumentParser(description='Load and display structs from a MATLAB file.')
    parser.add_argument('matfile', type=str, help='Path to the MATLAB file')
    args = parser.parse_args()

    mat_file = sio.loadmat(args.matfile)
    struct_names = [name for name in mat_file.keys() if isinstance(mat_file[name], np.ndarray)]

    if not struct_names:
        print("No structs found in the MATLAB file.")
    else:
        print("Available structs:")
        for name in struct_names:
            print(f"Struct: {name}")
            print(f"Data type: {mat_file[name].dtype}")
            print(f"Shape: {mat_file[name].shape}")

            if np.issubdtype(mat_file[name].dtype, np.integer):
                unique_values = np.unique(mat_file[name])
                print("Unique integer values:")
                print(unique_values)
            print()


if __name__ == "__main__":
    main()
