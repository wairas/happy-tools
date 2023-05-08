import re
import numpy as np

class Criteria:
    def __init__(self, operation, value=None, key=None, spectra_reader=None):
        self.operation = operation
        self.value = value
        self.key = key
        self.spectra_reader = spectra_reader
        
    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'operation': self.operation,
            'value' : self.value,
            'key': self.key
        }

    def check(self, x, y):
        z_data = self.spectra_reader.get_spectrum(x, y)
        if z_data is None:
            return False
        value = self.spectra_reader.json_reader.get_meta_data(x=x, y=y, key=self.key)
        
        if self.operation == 'equals':
            return value == self.value
        elif self.operation == 'in':
            return value in self.value
        elif self.operation == 'matches':
            return bool(re.search(self.value, value))
        elif self.operation == 'not_zero':
            return z_data != 0
        elif self.operation == 'no_outlier':
            z_data_mean = np.mean(z_data)
            z_data_std = np.std(z_data)
            return np.abs(z_data - z_data_mean) <= 2 * z_data_std
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")

class CriteriaGroup:
    def __init__(self, criteria_list=None):
        self.criteria_list = criteria_list or []

    def to_dict(self):
        json_dict = {
            'class': self.__class__.__name__,
        }
        if self.criteria_list:
            json_dict["criteria_list"]=[criteria.to_dict() for criteria in self.criteria_list ]
        return(json_dict)
        
    def check(self, x, y):
        return all(criteria.check(x, y) for criteria in self.criteria_list)

    def add_criteria(self, criteria):
        self.criteria_list.append(criteria)
