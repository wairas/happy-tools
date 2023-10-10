import ast
from seppl import get_class
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import Lars
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
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import SpectralClustering
from sklearn.cluster import DBSCAN
from sklearn.cluster import MeanShift
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
        for i, neighbors in enumerate(indices):
            X_neighbors = self.X_pls[neighbors]
            y_neighbors = self.y[neighbors]
            model = LinearRegression().fit(X_neighbors, y_neighbors)
            y_pred[i] = model.predict([X_pls[i]])
        return y_pred


REGRESSION_MODEL_MAP = {
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
}

CLASSIFICATION_MODEL_MAP = {
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
    "extra_trees": ExtraTreesClassifier,
}

CLUSTERING_MODEL_MAP = {
    'kmeans': KMeans,
    'agglomerative': AgglomerativeClustering,
    'spectral': SpectralClustering,
    'dbscan': DBSCAN,
    'meanshift': MeanShift,
}

MODEL_MAP = dict()
MODEL_MAP.update(REGRESSION_MODEL_MAP)
MODEL_MAP.update(CLASSIFICATION_MODEL_MAP)
MODEL_MAP.update(CLUSTERING_MODEL_MAP)


def create_model(model_name, model_params=None):
    """
    Create a scikit-learn model instance based on the given model_name and model_params.

    :param model_name: key from MODEL_MAP or full name of the scikit-learn model class.
    :type model_name: str
    :param model_params: Python dict string or dictionary containing the model hyperparameters
    :type model_params: str or dict
    :return: An instance of the scikit-learn model
    :rtype: BaseEstimator
    """

    if model_params is None:
        model_params = dict()
    if isinstance(model_params, str):
        params = ast.literal_eval(model_params)
    elif isinstance(model_params, dict):
        params = model_params
    else:
        raise Exception("Model parameters must be either a Python dictionary string or a dictionary with the parameters, but got: %s" % str(type(model_params)))

    # class name?
    try:
        c = get_class(full_class_name=model_name)
    except:
        # in model map?
        key = model_name.lower()
        if key not in MODEL_MAP:
            raise ValueError("Invalid sklearn method '" + model_name + "', neither class name nor key in model map (keys: " + ",".join(MODEL_MAP.keys()) + ")")
        else:
            c = MODEL_MAP[key]

    return c(**params)


# just for testing
if __name__ == "__main__":
    c = create_model("svm")
    print(type(c), c)
    c = create_model("dbscan", "{}")
    print(type(c), c)
    c = create_model("gaussiannb", "{'var_smoothing': 0.9}")
    print(type(c), c)
    c = create_model("sklearn.tree.DecisionTreeRegressor", {'max_depth': 4})
    print(type(c), c)
