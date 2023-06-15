import re
import numpy as np
from happy.core import ConfigurableObject


class Criteria(ConfigurableObject):

    def __init__(self, operation=None, value=None, key=None, spectra_reader=None):
        self.operation = operation
        self.value = value
        self.key = key
        self.spectra_reader = spectra_reader
        
    def to_dict(self):
        d = super().to_dict()
        d['operation'] = self.operation
        d['value'] = self.value
        d['key'] = self.key
        return d

    def from_dict(self, d):
        self.operation = d['operation']
        self.value = d['value']
        self.key = d['key']

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


class CriteriaGroup(ConfigurableObject):

    def __init__(self, criteria_list=None):
        self.criteria_list = criteria_list or []

    def to_dict(self):
        d = super().to_dict()
        if self.criteria_list:
            d["criteria_list"] = [criteria.to_dict() for criteria in self.criteria_list ]
        return d

    def from_dict(self, d):
        super().from_dict()
        if "criteria_list" in d:
            self.criteria_list = [Criteria.from_dict(x) for x in d["criteria_list"]]

    def check(self, x, y):
        return all(criteria.check(x, y) for criteria in self.criteria_list)

    def add_criteria(self, criteria):
        self.criteria_list.append(criteria)
