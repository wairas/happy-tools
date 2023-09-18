import re
import numpy as np


class Criteria:
    def __init__(self, operation, value=None, key=None):
        self.operation = operation
        self.value = value
        print(f"value: {value}")
        self.key = key
        print(f"key: {key}")
        
    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'operation': self.operation,
            'value' : self.value,
            'key': self.key
        }
        
    def __str__(self):
        return str(self.to_dict)
        
    def get_keys(self):
        return([self.key])

    def check(self, happy_data, x, y):
        z_data = happy_data.get_spectrum(x, y)
        if z_data is None:
            return False
        value = happy_data.get_meta_data(x=x, y=y, key=self.key)
        if self.operation == 'not_missing':
            return value is not None
        if self.operation == 'equals':
            return value == self.value
        elif self.operation == 'greater_than':
            return value > self.value
        elif self.operation == 'not_in':
            return value not in self.value
        elif self.operation == 'in':
            #print(f"key: {self.key}  self.value:{self.value}")
            return value in self.value
        elif self.operation == 'matches':
            return bool(re.search(self.value, value))
        elif self.operation == 'spectrum_not_zero':
            return (z_data != 0).all()
        elif self.operation == 'not_outlier':
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
        
    def __str__(self):
        return str(self.to_dict())
        
    def check(self, happy_data, x, y):
        #for criteria in self.criteria_list:
        #    result = criteria.check(happy_data, x, y)
        #    print(result)
        return all(criteria.check(happy_data, x, y) for criteria in self.criteria_list)
     
    def get_keys(self):
        return([c.key for c in self.criteria_list])

    def add_criteria(self, criteria):
        self.criteria_list.append(criteria)
        
    def __iter__(self):
        return iter(self.criteria_list)
