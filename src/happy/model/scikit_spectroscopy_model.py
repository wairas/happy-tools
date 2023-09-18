import os
import ast
import pickle
from happy.model.spectroscopy_model import SpectroscopyModel
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, Lars
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.cross_decomposition import PLSRegression
from sklearn.neighbors import KNeighborsRegressor
#from xgboost import XGBClassifier
#from lightgbm import LGBMClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin


class PlsFilteredKnnRegression(BaseEstimator, RegressorMixin):
    def __init__(self, n_components=15, n_neighbors=150):
        self.n_components = n_components
        self.n_neighbors = n_neighbors

    def fit(self, X, y):
        # Fit PLS regression on X and y
        pls = PLSRegression(n_components=self.n_components)
        pls.fit(X, y)
        # Get the PLS components for X
        self.X_pls = pls.transform(X)
        self.y = np.array(y) #y
        # Fit k-NN regression on the PLS components
        knn = KNeighborsRegressor(n_neighbors=self.n_neighbors)
        knn.fit(self.X_pls, y)
        self.pls_ = pls
        self.knn_ = knn
        return self

    def predict(self, X):
        # Transform X using PLS
        X_pls = self.pls_.transform(X)
        # Find the k-nearest neighbors in the PLS-transformed space
        _, indices = self.knn_.kneighbors(X_pls)
        # Predict the output variables for each input example using linear regression
        y_pred = np.empty((X_pls.shape[0], 1))
        #print(indices)
        for i, neighbors in enumerate(indices):
            #print(i)
            #print(neighbors)
            #print(neighbors.shape)
            #print(type(neighbors))
            #print(len(self.y))
            X_neighbors = self.X_pls[neighbors]
            y_neighbors = self.y[neighbors]
            model = LinearRegression().fit(X_neighbors, y_neighbors)
            y_pred[i] = model.predict([X_pls[i]])
        return y_pred


class ScikitSpectroscopyModel(SpectroscopyModel):
    def __init__(self, data_folder, target, happy_preprocessor=None, additional_meta_data=None, pixel_selector=None, model=None, training_data = None, mapping=None):
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
        return(self.training_data)
        
    def one_hot_encode(self, data):
        if isinstance(data, list):
            print(len(data))
            print(data[0].shape)
            data = [self._one_hot_encode_array(arr) for arr in data]
            #data = np.stack(data)
        else:
            data = self._one_hot_encode_array(data)
        
        return data

    def _one_hot_encode_array(self, array):
        if array.shape[-1] != 1:
            expanded_array = np.expand_dims(array, axis=-1)  # Add an extra dimension for encoding
        else:
            expanded_array = array
            
        print("Expanded Array Shape:", expanded_array.shape)
        
        # Create an array of zeros with the desired shape for one-hot encoding
        encoded_data = np.zeros((*expanded_array.shape, self.num_classes), dtype=int)
        
        print("Encoded Data Shape (before reshape):", encoded_data.shape)
        
        # Reshape the encoded_data array to have the same shape as expanded_array for indexing
        encoded_data = encoded_data.reshape(-1, self.num_classes)
        
        try:
            for i in range(encoded_data.shape[0]):
                encoded_data[i, expanded_array.reshape(-1)[i]] = 1
        except Exception as e:
            print("Error:", e)
        
        # Reshape the encoded_data array back to its original shape
        encoded_data = encoded_data.reshape(*expanded_array.shape, self.num_classes)
        print(encoded_data.shape)
        return encoded_data

    def fit(self, sample_ids, force=False, keep_training_data=False):
        if self.training_data is None or Force or keep_training_data:
            self.training_data = self.generate_training_dataset(sample_ids)
        # Implement logic to fit the scikit-learn model using training_data
        # Assuming the model is already initialized in self.model

        self.model.fit(self.training_data["X_train"], self.training_data["y_train"])
        print("in fit")

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

    @classmethod
    def create_model(cls, method_name, model_params):
        """
        Create a scikit-learn model instance based on the given model_name and model_params.

        Args:
            model_name (str): Name of the scikit-learn model class (e.g., 'LinearRegression', 'Ridge', 'Lasso', etc.).
            model_params (dict): Dictionary containing the model hyperparameters.

        Returns:
            BaseEstimator: An instance of the scikit-learn model.
        """
        model_map = {
            # Regression models
            'linearregression': LinearRegression,
            'ridge': Ridge,
            'lars': Lars,
            'plsregression': PLSRegression, 
            'plsneighbourregression': PlsFilteredKnnRegression, 
            'lasso': Lasso,
            'elasticnet': ElasticNet,
            'decisiontreeregressor': DecisionTreeRegressor,
            'randomforestregressor': RandomForestRegressor,
            'svr': SVR,
            # Classification models
            'randomforestclassifier': RandomForestClassifier,
            'gradientboostingclassifier': GradientBoostingClassifier,
            'adaboostclassifier': AdaBoostClassifier,
            'kneighborsclassifier': KNeighborsClassifier,
            'decisiontreeclassifier': DecisionTreeClassifier,
            'gaussiannb': GaussianNB,
            'logisticregression': LogisticRegression,
            'mlpclassifier': MLPClassifier,
            "svm": SVC,
            "random_forest": RandomForestClassifier,
            "knn": KNeighborsClassifier,
            "decision_tree": DecisionTreeClassifier,
            "gradient_boosting": GradientBoostingClassifier,
            "naive_bayes": GaussianNB,
            "logistic_regression": LogisticRegression,
            "neural_network": MLPClassifier,
            "adaboost": AdaBoostClassifier,
            "extra_trees": ExtraTreesClassifier
            # Add more models to the map as needed
        }

        regression_params = ast.literal_eval(model_params)
        
        method_name = method_name.lower()
        if method_name not in model_map:
            raise ValueError(f"Invalid regression method: {method_name}")

        regression_class = model_map[method_name]
        return regression_class(**regression_params)
