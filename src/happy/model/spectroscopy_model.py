import abc
from happy.readers.happy_reader import HappyReader
from happy.model.happy_model import HappyModel


class SpectroscopyModel(HappyModel, abc.ABC):
    def __init__(self, data_folder, target, happy_preprocessor=None, additional_meta_data=None, pixel_selector=None):
        super().__init__(data_folder, target, happy_preprocessor, additional_meta_data)
        self.pixel_selector = pixel_selector
        print("ps")
        print(pixel_selector)

    def _generate_full_prediction_dataset(self, sample_ids, return_actuals=False):
        dataset = {"X_pred": [], "y_pred": [],"sample_id": [], "x":[], "y":[]}
        happy_reader = HappyReader(self.data_folder)
        added_wavelengths = False
        for sample_id in sample_ids:
            # Load HappyData using HappyReader
            happy_data_list = happy_reader.load_data(sample_id)
            for happy_data in happy_data_list:
                # Apply HappyPreprocessor if available
                
                if self.happy_preprocessor is not None:
                    happy_data = happy_data.apply_preprocess(self.happy_preprocessor)
                if not added_wavelengths:
                    dataset['wavelengths']=happy_data.get_wavelengths()
                    added_wavelengths = True
                    
                reshaped_hsi_data = happy_data.get_numpy_yx().reshape(-1, happy_data.get_numpy_yx().shape[2])
                target_value = happy_data.get_meta_data(key=self.target)
                
                dataset["X_pred"].append(reshaped_hsi_data)
                if return_actuals:
                    dataset["y_pred"].append(target_value)
                dataset["x"].append(happy_data.get_numpy_yx().shape[1])
                dataset["y"].append(happy_data.get_numpy_yx().shape[0])
                #dataset["y_pred"].append(target_value)
                #dataset["sample_id"].append(happy_data.get_full_id())
        return dataset
        
    def _generate_dataset(self, sample_ids, is_train=True, return_actuals=False):
        dataset = {"X_train": [], "y_train": [], "sample_id": []} if is_train else {"X_pred": [], "y_pred": [],"sample_id": []}
        happy_reader = HappyReader(self.data_folder)

        added_wavelengths = False
        for sample_id in sample_ids:
            # Load HappyData using HappyReader
            happy_data_list = happy_reader.load_data(sample_id)
            for happy_data in happy_data_list:
                # Apply HappyPreprocessor if available
                
                if self.happy_preprocessor is not None:
                    happy_data = happy_data.apply_preprocess(self.happy_preprocessor)
                if not added_wavelengths:
                    dataset['wavelengths']=happy_data.get_wavelengths()
                    added_wavelengths = True
                # Apply PixelSelector and collect pixels
                selected_pixels = self.pixel_selector.select_pixels(happy_data)
                
                for ind, (x, y, z_data) in enumerate(selected_pixels):
                    # Check if the target value is not missing for the pixel
                    target_value = happy_data.get_meta_data(x=x, y=y, key=self.target)
                    #print(type(target_value))
                    if target_value is not None and is_train:
                        dataset["X_train"].append(z_data)
                        dataset["y_train"].append(target_value)
                        dataset["sample_id"].append(happy_data.get_full_id())
                    elif not is_train:
                        dataset["X_pred"].append(z_data)
                        dataset["y_pred"].append(target_value)
                        dataset["sample_id"].append(happy_data.get_full_id())
        return dataset

    def generate_training_dataset(self, sample_ids):
        return self._generate_dataset(sample_ids, is_train=True)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        if pixel_selector is None:
            pixel_selector = self.pixel_selector

        return self._generate_dataset(sample_ids, is_train=False)
