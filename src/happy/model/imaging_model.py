from happy.readers.happy_reader import HappyReader
from happy.model.happy_model import HappyModel
import itertools


class ImagingModel(HappyModel):
    def __init__(self, data_folder, target, happy_preprocessor=None, additional_meta_data=None, region_selector=None):
        super().__init__(data_folder, target, happy_preprocessor, additional_meta_data)
        self.region_selector = region_selector
        self.data_shape = None
        
    def get_data_shape(self):
        print(f"data shape: {self.data_shape}")
        return(self.data_shape)

    def generate_batch(self, sample_ids, batch_size, is_train=True, loop=False, return_actuals=False):
        # Get the preprocessed data
        #X = self.preprocess_data()
        happy_reader = HappyReader(self.data_folder)
        # Apply region selection based on the sample_ids
        if self.region_selector is None:
            raise ValueError("Region selector is not set. Use set_region_selector() method to set the region selector.")
        added_wavelengths = False
        dataset = {"X_train": [], "y_train": [], "sample_id": []} if is_train else {"X_pred": [], "y_pred": [], "sample_id": []}
        sample_id_iterator = itertools.cycle(sample_ids) if loop else sample_ids
        for sample_id in sample_id_iterator:
            happy_data_list = happy_reader.load_data(sample_id)
            for happy_data in happy_data_list:
                # Apply HappyPreprocessor if available
                
                if self.happy_preprocessor is not None:
                    happy_data = happy_data.apply_preprocess(self.happy_preprocessor)
                
                region_list = self.region_selector.extract_regions(happy_data)
                for region in region_list:
                    if not added_wavelengths:
                        dataset['wavelengths']=happy_data.get_wavelengths()
                        added_wavelengths = True
                    if self.data_shape is None:
                        self.data_shape = region.get_numpy_yx().shape
                        print(f"*********************************data shape: {self.data_shape}")
                    # Extract the target variable from the metadata (assuming the target is stored in the metadata)
                    target_value = self.get_y(happy_data)
                                
                    if is_train:
                        if target_value is None:
                            continue
                        dataset["X_train"].append(region)
                        dataset["y_train"].append(target_value)
                        dataset["sample_id"].append(sample_id)
                    else:
                        if return_actuals:
                            dataset["y_pred"].append(target_value)
                        dataset["X_pred"].append(region.get_numpy_yx())
                        dataset["sample_id"].append(sample_id)

                    # Check if the batch size is reached, then yield the batch
                    if len(dataset["X_train"]) == batch_size:
                        yield dataset
                        dataset = {"X_train": [], "y_train": [], "sample_id": []} if is_train else {"X_pred": [], "y_pred": [],  "sample_id": []}

            # Yield the last batch (if it's not a full batch)
            if dataset["X_train"]:
                yield dataset
    
    def _generate_dataset(self, sample_ids, is_train=True, return_actuals=False):
        dataset = {"X_train": [], "y_train": [], "sample_id": []} if is_train else {"X_pred": [], "y_pred": [], "sample_id": []}
        happy_reader = HappyReader(self.data_folder)
        # Apply region selection based on the sample_ids
        if self.region_selector is None:
            raise ValueError("Region selector is not set. Use set_region_selector() method to set the region selector.")
        added_wavelengths = False
        for sample_id in sample_ids:
            happy_data_list = happy_reader.load_data(sample_id)
            for happy_data in happy_data_list:
                # Apply HappyPreprocessor if available
                
                if self.happy_preprocessor is not None:
                    happy_data = happy_data.apply_preprocess(self.happy_preprocessor)
                
                region_list = self.region_selector.extract_regions(happy_data)
                for region in region_list:
                    if not added_wavelengths:
                        dataset['wavelengths']=happy_data.get_wavelengths()
                        added_wavelengths = True
                    if self.data_shape is None:
                        self.data_shape = region.get_numpy_yx().shape
                    # Extract the target variable from the metadata (assuming the target is stored in the metadata)                  
                    
                    if is_train:
                        target_value = self.get_y(happy_data)
                        if target_value is None:
                            continue
                        dataset["X_train"].append(region.get_numpy_yx())
                        dataset["y_train"].append(target_value)
                        dataset["sample_id"].append(region.sample_id)
                    else:
                        if return_actuals:
                            target_value = self.get_y(happy_data)
                            dataset["y_pred"].append(target_value)
                        dataset["X_pred"].append(region.get_numpy_yx())
                        dataset["sample_id"].append(sample_id)

        return dataset

    def generate_training_dataset(self, sample_ids):
        return self._generate_dataset(sample_ids, is_train=True)

    def generate_prediction_dataset(self, sample_ids, pixel_selector=None, return_actuals=False):
        return self._generate_dataset(sample_ids, is_train=False, return_actuals=return_actuals)

    def set_region_selector(self, region_selector):
        self.region_selector = region_selector

