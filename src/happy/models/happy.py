import abc
import pickle

from happy.base.core import ObjectWithLogging


class HappyModel(ObjectWithLogging, abc.ABC):
    def __init__(self, data_folder, target, happy_preprocessor=None, additional_meta_data=None):
        super().__init__()
        self.data_folder = data_folder
        self.happy_preprocessor = happy_preprocessor
        self.target = target
        self.additional_meta_data = additional_meta_data

    def preprocess_data(self, happy_data):
        if self.happy_preprocessor is None:
            raise ValueError("Preprocessor is not set. Use set_preprocessor() method to set the preprocessor.")
        return self.happy_preprocessor.apply(happy_data)

    def fit(self, id_list, target_variable):
        raise NotImplementedError("Subclasses must implement the train method.")

    def predict(self, id_list, return_actuals=False):
        raise NotImplementedError("Subclasses must implement the predict method.")

    def save(self, filepath):
        with open(filepath, 'wb') as file:
            pickle.dump(self, file)

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as file:
            return pickle.load(file)

    # ... (other methods)
