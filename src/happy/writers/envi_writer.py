import os
import spectral.io.envi as envi
from .base_writer import BaseWriter


class EnviWriter(BaseWriter):
    def __init__(self, output_folder):
        super().__init__(output_folder)

    def write_data(self, data, filename, datatype=None, wavelengths=None):
        filepath = os.path.join(self.output_folder, filename)
        print("write "+filename)
        print(data.shape)
        if datatype is None:
            print("is none")
            datatype = data.dtype.name
        print(datatype)
        envi.save_image(filepath, data, dtype=datatype, force=True, interleave='BSQ', metadata={'wavelength': wavelengths})
