import pickle
import ast
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering, DBSCAN, MeanShift
from happy.model.spectroscopy_model import SpectroscopyModel


class UnsupervisedPixelClusterer(SpectroscopyModel):
    def __init__(self, data_folder, target, clusterer_name, clusterer_params={}, happy_preprocessor=None, additional_meta_data=None, pixel_selector=None):
        #self.num_clusters = num_clusters
        super().__init__(data_folder, target, happy_preprocessor, additional_meta_data, pixel_selector)
        
        self.clusterer_name = clusterer_name
        self.clusterer_params = ast.literal_eval(clusterer_params)

        self.clusterer = None

    def create_clusterer(self):
        if self.clusterer_name == 'kmeans':
            return KMeans(**self.clusterer_params)
        elif self.clusterer_name == 'agglomerative':
            return AgglomerativeClustering(**self.clusterer_params)
        elif self.clusterer_name == 'spectral':
            return SpectralClustering(**self.clusterer_params)
        elif self.clusterer_name == 'dbscan':
            return DBSCAN(**self.clusterer_params)
        elif self.clusterer_name == 'meanshift':
            return MeanShift(**self.clusterer_params)
        else:
            raise ValueError("Invalid clustering method name.")

    def fit(self, id_list, target_variable=None):
        # no target values..
        training_dataset = self.generate_prediction_dataset(id_list, return_actuals=False)
        X_train = np.array(training_dataset["X_pred"])
        self.clusterer = self.create_clusterer()
        self.clusterer.fit(X_train)

    def predict(self, id_list, return_actuals=False):
        if self.clusterer is None:
            raise ValueError("Clusterer has not been trained. Call the fit method first.")
        # Load and preprocess data for prediction
        prediction_dataset = self.generate_prediction_dataset(id_list, return_actuals=return_actuals)
        X_pred = np.array(prediction_dataset["X_pred"])
        predictions = self.clusterer.predict(X_pred)
        if return_actuals:
            return predictions, np.array(X_pred["y_pred"])
        else:
            return predictions,None

    def predict_images(self, sample_ids, return_actuals=False):
        predictions_list = []
        res = self._generate_full_prediction_dataset(sample_ids, return_actuals)
        plist = res["X_pred"]
        if return_actuals:
            ylist = res["y_pred"]
            actuals_list = []
        for i, zarray in enumerate(plist):
            predictions = self.clusterer.predict(zarray)
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

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as file:
            return pickle.load(file)
"""
# Example usage
num_clusters = 5
data_folder = "path/to/your/data"
target = "target_variable_name"
clusterer_name = 'kmeans'
clusterer_params = {'n_clusters': num_clusters, 'random_state': 0}
clusterer = UnsupervisedPixelClusterer(num_clusters, data_folder, target, clusterer_name, clusterer_params)
clusterer.fit()

# Now you can use the trained clusterer for prediction or other tasks
cluster_labels = clusterer.predict(id_list)
print("Cluster labels:", cluster_labels)
"""