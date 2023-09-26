import time
from happy.base.core import load_class
from happy.model.spectroscopy_model import SpectroscopyModel
from happy.model.imaging_model import ImagingModel


class GenericSpectroscopyModel(SpectroscopyModel):
    def __init__(self, base_model, model_path, model_class_name):
        super().__init__(None, None, None, None, None)
        self.base_model = base_model
        self.model_path = model_path
        self.model_class_name = model_class_name

    def preprocess_data(self, happy_data):
        return self.base_model.preprocess_data(happy_data)

    def fit(self, id_list, target_variable):
        self.base_model.fit(id_list, target_variable)

    def predict(self, id_list, return_actuals=False):
        return self.base_model(id_list, return_actuals)

    def generate_training_dataset(self, sample_ids):
        return self.base_model.generate_training_dataset(sample_ids)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self.base_model.generate_prediction_dataset(sample_ids, pixel_selector, return_actuals)

    @classmethod
    def instantiate(cls, model_path, model_class_name, data_folder, target):
        c = load_class(model_path, "happy.generic_spectroscopy_model." + str(int(round(time.time() * 1000))), model_class_name)
        if not issubclass(c, SpectroscopyModel):
            raise Exception("Class '%s' in '%s' not of type '%s'!" % (model_class_name, model_path, str(SpectroscopyModel)))
        base_model = c(data_folder, target)
        return GenericSpectroscopyModel(base_model, model_path, model_class_name)


class GenericImagingModel(ImagingModel):
    def __init__(self, base_model, model_path, model_class_name):
        super().__init__(self, None, None, None, None)
        self.base_model = base_model
        self.model_path = model_path
        self.model_class_name = model_class_name

    def generate_batch(self, sample_ids, batch_size, is_train=True, loop=False, return_actuals=False):
        for item in self.base_model.generate_batch(sample_ids, batch_size, is_train, loop, return_actuals):
            yield item

    def generate_training_dataset(self, sample_ids):
        return self.base_model.generate_training_dataset(sample_ids)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self.base_model.generate_prediction_dataset(sample_ids, pixel_selector, return_actuals)

    def set_region_selector(self, region_selector):
        self.base_model.set_region_selector(region_selector)

    def preprocess_data(self, happy_data):
        return self.base_model.preprocess_data(happy_data)

    def get_data_shape(self):
        return self.base_model.get_data_shape()

    def get_y(self, happy_data):
        return self.base_model.get_y(happy_data)

    def fit(self, id_list, target_variable):
        self.base_model.fit(id_list, target_variable)

    def predict(self, id_list, return_actuals=False):
        return self.base_model.predict(id_list, return_actuals)

    @classmethod
    def instantiate(cls, model_path, model_class_name, data_folder, target):
        c = load_class(model_path, "happy.generic_imaging_model." + str(int(round(time.time() * 1000))), model_class_name)
        if not issubclass(c, ImagingModel):
            raise Exception("Class '%s' in '%s' not of type '%s'!" % (model_class_name, model_path, str(ImagingModel)))
        base_model = c(data_folder, target)
        return GenericImagingModel(base_model, model_path, model_class_name)
