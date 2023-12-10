import os
import pickle

import numpy as np

from happy.models.spectroscopy import SpectroscopyModel


class ScikitSpectroscopyModel(SpectroscopyModel):
    def __init__(self, data_folder, target, happy_preprocessor=None, additional_meta_data=None, pixel_selector=None, model=None, training_data=None, mapping=None):
        super().__init__(data_folder, target, happy_preprocessor, additional_meta_data, pixel_selector)
        self.model = model
        self.training_data = training_data
        
        # Extract values from the dictionary
        if mapping is not None:
            values = mapping.values()
            # Convert values to a list and get unique values
            unique_values = set(values)
            # Count the number of unique values
            self.num_classes = len(unique_values)

    def get_training_data(self):
        return self.training_data
        
    def one_hot_encode(self, data):
        if isinstance(data, list):
            self.logger().info(len(data))
            self.logger().info(data[0].shape)
            data = [self._one_hot_encode_array(arr) for arr in data]
        else:
            data = self._one_hot_encode_array(data)
        
        return data

    def _one_hot_encode_array(self, array):
        if array.shape[-1] != 1:
            expanded_array = np.expand_dims(array, axis=-1)  # Add an extra dimension for encoding
        else:
            expanded_array = array
            
        self.logger().info("Expanded Array Shape:", expanded_array.shape)
        
        # Create an array of zeros with the desired shape for one-hot encoding
        encoded_data = np.zeros((*expanded_array.shape, self.num_classes), dtype=int)
        
        self.logger().info("Encoded Data Shape (before reshape):", encoded_data.shape)
        
        # Reshape the encoded_data array to have the same shape as expanded_array for indexing
        encoded_data = encoded_data.reshape(-1, self.num_classes)
        
        try:
            for i in range(encoded_data.shape[0]):
                encoded_data[i, expanded_array.reshape(-1)[i]] = 1
        except Exception:
            self.logger().exception("Error:")
        
        # Reshape the encoded_data array back to its original shape
        encoded_data = encoded_data.reshape(*expanded_array.shape, self.num_classes)
        self.logger().info(encoded_data.shape)
        return encoded_data

    def fit(self, sample_ids, force=False, keep_training_data=False):
        if self.training_data is None or force or keep_training_data:
            self.training_data = self.generate_training_dataset(sample_ids)
        # Implement logic to fit the scikit-learn model using training_data
        # Assuming the model is already initialized in self.model

        self.model.fit(self.training_data["X_train"], self.training_data["y_train"])
        self.logger().info("in fit")

    def predict(self, sample_ids, prediction_pixel_selector=None, prediction_data=None):
        
        if prediction_data is None:
            prediction_data = self.generate_prediction_dataset(pixel_selector=prediction_pixel_selector)
        # Implement logic to predict using the scikit-learn model
        predictions = self.model.predict(prediction_data["X_pred"])
        return predictions

    def predict_images(self, sample_ids, return_actuals=False):
        predictions_list = []
        res = self._generate_full_prediction_dataset(sample_ids, return_actuals)
        plist = res["X_pred"]
        ylist = None
        actuals_list = None
        if return_actuals:
            ylist = res["y_pred"]
            actuals_list = []
        for i, zarray in enumerate(plist):
            predictions = self.model.predict(zarray)
            # Reshape predicted labels to match the original image size (y, x)
            prediction_array = predictions.reshape(res["y"][i], res["x"][i])  
            # Append the prediction array to the list
            predictions_list.append(prediction_array)
            
            if return_actuals:
                acts = ylist[i]
                acts_array = acts.reshape(res["y"][i], res["x"][i])  
                actuals_list.append(acts_array)
        if return_actuals:
            return predictions_list, actuals_list
        else:
            return predictions_list,None   
        """
        if return_actuals:
            return predictions_list, np.array(res["y_pred"])
        else:
            return predictions_list,None
        #return(predictions_list)
        """
    
    def save_model(self, folder_name, save_training_data=True):
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        model_info = {
            'data_folder': self.data_folder,
            'target': self.target,
            'happy_preprocessor': self.happy_preprocessor,
            'additional_meta_data': self.additional_meta_data,
            'pixel_selector': self.pixel_selector,
            'model': self.model,
            'training_data': self.training_data if save_training_data else None,
            # Add any other parameters that need to be saved
        }

        model_filepath = os.path.join(folder_name, 'model.pkl')
        with open(model_filepath, "wb") as f:
            pickle.dump(model_info, f)

        # Save the model hyperparameters separately to a params file
        params_filepath = os.path.join(folder_name, 'model_params.pkl')
        with open(params_filepath, "wb") as f:
            pickle.dump(self.model.get_params(), f)
            
        # Generate Python script to load the model
        script_filepath = os.path.join(folder_name, 'load_model.py')
        with open(script_filepath, 'w') as f:
            f.write("# Load the model\n")
            f.write(f"import os\n")
            f.write(f"import sys\n")
            f.write(f"from {self.__class__.__module__} import {self.__class__.__name__}\n")
            f.write(f"folder_name = '{os.path.abspath(folder_name)}'\n")
            f.write(f"model = {self.__class__.__name__}.load_model(folder_name)\n")

    @classmethod
    def load_model(cls, folder_name):
        model_filepath = os.path.join(folder_name, 'model.pkl')
        with open(model_filepath, "rb") as f:
            model_info = pickle.load(f)

        loaded_model = cls(model_info['data_folder'], model_info['target'], 
                           happy_preprocessor=model_info['happy_preprocessor'],
                           additional_meta_data=model_info['additional_meta_data'],
                           pixel_selector=model_info['pixel_selector'],
                           model=model_info['model'],
                           training_data=model_info['training_data'])

        # Load the model hyperparameters from the params file and set them
        params_filepath = os.path.join(folder_name, 'model_params.pkl')
        with open(params_filepath, "rb") as f:
            model_params = pickle.load(f)

        loaded_model.model.set_params(**model_params)

        return loaded_model
