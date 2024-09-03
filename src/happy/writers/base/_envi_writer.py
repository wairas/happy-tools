import os
import spectral.io.envi as envi
from ._base_writer import BaseWriter


class EnviWriter(BaseWriter):
    def __init__(self, output_folder):
        super().__init__(output_folder)

    def write_data(self, data, filename, datatype=None, wavelengths=None):
        filepath = os.path.join(self.output_folder, filename)
        self.logger().info("write: " + filename)
        self.logger().info(data.shape)
        if datatype is None:
            self.logger().info("data type is none")
            datatype = data.dtype.name
        self.logger().info(datatype)
        envi.save_image(filepath, data, dtype=datatype, force=True, interleave='BSQ', metadata={'wavelength': wavelengths})
