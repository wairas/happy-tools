import numpy as np
import os
import scipy.io as sio
from happy.writers.base_writer import BaseWriter


class MatWriter(BaseWriter):
    def __init__(self, output_folder):
        super().__init__(output_folder)
        self.meta_list = None

    def write_data(self, data, filename, wavelengths=None):
        filepath = os.path.join(self.output_folder, filename)
        save_dic = {'data': data, 'lambda': wavelengths}
        
        if self.meta_list is not None:
            for metadata_name in self.meta_list:
                y_dim, x_dim, _ = data.shape

                # Create an empty numpy array to store the metadata values
                metadata_array = np.empty((y_dim, x_dim))

                # Iterate over each (y, x) coordinate and populate the array with metadata values
                for y in range(y_dim):
                    for x in range(x_dim):
                        # TODO self.get_meta_data does not exist?
                        metadata_value = self.get_meta_data(x=x, y=y, key=metadata_name)
                        metadata_array[y, x] = metadata_value
                            
                save_dic[metadata_name] = metadata_array

        sio.savemat(filepath, save_dic)

    def set_meta_list(self, mlist):
        self.meta_list = mlist
