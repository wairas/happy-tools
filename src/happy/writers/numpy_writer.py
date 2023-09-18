import json
import os
import numpy as np
from .base_writer import BaseWriter


def check_ragged_data(data):
    print(data)
    #print(data.shape)
    first_shape = data[0].shape
    for i, array in enumerate(data):
        if array.shape != first_shape:
            print("Data contains arrays with different shapes.")
            print("Shape of the first array:", first_shape)
            print("Index:", i, "Shape:", array.shape)
            return False
    print("Data is consistent. All arrays have the same shape:", first_shape)
    return True


class NumpyWriter(BaseWriter):
    def __init__(self, output_folder):
        super().__init__(output_folder)

    def write(self, data, filename, wavelengths=None):
        filepath = os.path.join(self.output_folder, filename)
        is_ragged = check_ragged_data(data)
        np.save(filepath, data)

        if wavelengths is not None:
            json_filepath = os.path.splitext(filepath)[0] + '.json'
            with open(json_filepath, 'w') as f:
                json.dump(wavelengths.tolist(), f)
