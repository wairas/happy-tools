from happy.base.core import ObjectWithLogging


class BaseWriter(ObjectWithLogging):
    def __init__(self, output_folder):
        super().__init__()
        self.output_folder = output_folder

    def write_data(self, data, filename, datatype_mapping=None):
        raise NotImplementedError("Subclasses must implement the write_data method.")
