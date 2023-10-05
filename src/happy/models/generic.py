from happy.models.spectroscopy import SpectroscopyModel
from happy.models.scikit_spectroscopy import ScikitSpectroscopyModel
from happy.models.unsupervised_pixel_clusterer import UnsupervisedPixelClusterer
from happy.models.imaging import ImagingModel


class GenericSpectroscopyModel(SpectroscopyModel):
    def __init__(self, base_model):
        super().__init__(None, None, None, None, None)
        self.base_model = base_model

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
    def instantiate(cls, c, data_folder, target):
        if not issubclass(c, SpectroscopyModel):
            raise Exception("Class '%s' not of type '%s'!" % (str(c), str(SpectroscopyModel)))
        base_model = c(data_folder, target)
        return GenericSpectroscopyModel(base_model)


class GenericScikitSpectroscopyModel(ScikitSpectroscopyModel):
    def __init__(self, base_model):
        super().__init__(None, None, happy_preprocessor=None, additional_meta_data=None,
                         pixel_selector=None, model=None, training_data=None, mapping=None)
        self.base_model = base_model

    def preprocess_data(self, happy_data):
        return self.base_model.preprocess_data(happy_data)

    def fit(self, sample_ids, force=False, keep_training_data=False):
        self.base_model.fit(sample_ids, force=force, keep_training_data=keep_training_data)

    def get_training_data(self):
        return self.base_model.get_training_data()

    def predict(self, sample_ids, prediction_pixel_selector=None, prediction_data=None):
        return self.base_model.predict(sample_ids, prediction_pixel_selector=prediction_pixel_selector, prediction_data=prediction_data)

    def predict_images(self, sample_ids, return_actuals=False):
        return self.base_model.predict_images(sample_ids, return_actuals=return_actuals)

    def generate_training_dataset(self, sample_ids):
        return self.base_model.generate_training_dataset(sample_ids)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self.base_model.generate_prediction_dataset(sample_ids, pixel_selector=pixel_selector, return_actuals=return_actuals)

    def save_model(self, folder_name, save_training_data=True):
        # TODO wrap in Generic?
        self.base_model.save_model(folder_name, save_training_data=save_training_data)

    @classmethod
    def instantiate(cls, c, data_folder, target):
        if not issubclass(c, ScikitSpectroscopyModel):
            raise Exception("Class '%s' not of type '%s'!" % (str(c), str(ScikitSpectroscopyModel)))
        base_model = c(data_folder, target)
        return GenericScikitSpectroscopyModel(base_model)


class GenericUnsupervisedPixelClusterer(UnsupervisedPixelClusterer):
    def __init__(self, base_model):
        super().__init__(None, None, None, happy_preprocessor=None, additional_meta_data=None, pixel_selector=None)
        self.base_model = base_model

    def preprocess_data(self, happy_data):
        return self.base_model.preprocess_data(happy_data)

    def generate_training_dataset(self, sample_ids):
        return self.base_model.generate_training_dataset(sample_ids)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self.base_model.generate_prediction_dataset(sample_ids, pixel_selector, return_actuals)

    def fit(self, id_list, target_variable=None):
        self.base_model.fit(id_list, target_variable=target_variable)

    def predict(self, id_list, return_actuals=False):
        return self.base_model.predict(id_list, return_actuals=return_actuals)

    def predict_images(self, sample_ids, return_actuals=False):
        return self.base_model.predict_images(sample_ids, return_actuals=return_actuals)

    @classmethod
    def instantiate(cls, c, data_folder, target):
        if not issubclass(c, UnsupervisedPixelClusterer):
            raise Exception("Class '%s' not of type '%s'!" % (str(c), str(UnsupervisedPixelClusterer)))
        base_model = c(data_folder, target)
        return GenericUnsupervisedPixelClusterer(base_model)


class GenericImagingModel(ImagingModel):
    def __init__(self, base_model):
        super().__init__(self, None, None, None, None)
        self.base_model = base_model

    def generate_batch(self, sample_ids, batch_size, is_train=True, loop=False, return_actuals=False):
        for item in self.base_model.generate_batch(sample_ids, batch_size, is_train=is_train, loop=loop, return_actuals=return_actuals):
            yield item

    def generate_training_dataset(self, sample_ids):
        return self.base_model.generate_training_dataset(sample_ids)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self.base_model.generate_prediction_dataset(sample_ids, pixel_selector=pixel_selector, return_actuals=return_actuals)

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
        return self.base_model.predict(id_list, return_actuals=return_actuals)

    @classmethod
    def instantiate(cls, c, data_folder, target):
        if not issubclass(c, ImagingModel):
            raise Exception("Class '%s' not of type '%s'!" % (str(c), str(ImagingModel)))
        base_model = c(data_folder, target)
        return GenericImagingModel(base_model)
