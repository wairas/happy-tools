import re
import numpy as np

OPERATION_NOT_MISSING = "not_missing"
OPERATION_EQUALS = "equals"
OPERATION_GREATER_THAN = "greater_than"
OPERATION_NOT_IN = "not_in"
OPERATION_IN = "in"
OPERATION_MATCHES = "matches"
OPERATION_SPECTRUM_NOT_ZERO = "spectrum_not_zero"
OPERATION_NOT_OUTLIER = "not_outlier"
OPERATIONS = [
    OPERATION_NOT_MISSING,
    OPERATION_EQUALS,
    OPERATION_GREATER_THAN,
    OPERATION_NOT_IN,
    OPERATION_IN,
    OPERATION_MATCHES,
    OPERATION_SPECTRUM_NOT_ZERO,
    OPERATION_NOT_OUTLIER,
]


class Criteria:
    def __init__(self, operation, value=None, key=None):
        if operation not in OPERATIONS:
            raise Exception("Unknown operation: %s" % operation)
        self.operation = operation
        self.value = value
        self.key = key

    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'operation': self.operation,
            'value': self.value,
            'key': self.key
        }
        
    def __str__(self):
        return str(self.to_dict())
        
    def get_keys(self):
        return [self.key]

    def check(self, happy_data, x, y):
        z_data = happy_data.get_spectrum(x, y)
        if z_data is None:
            return False
        value = happy_data.get_meta_data(x=x, y=y, key=self.key)
        if self.operation == OPERATION_NOT_MISSING:
            return value is not None
        if self.operation == OPERATION_EQUALS:
            return value == self.value
        elif self.operation == OPERATION_GREATER_THAN:
            return value > self.value
        elif self.operation == OPERATION_NOT_IN:
            return value not in self.value
        elif self.operation == OPERATION_IN:
            return value in self.value
        elif self.operation == OPERATION_MATCHES:
            return bool(re.search(self.value, value))
        elif self.operation == OPERATION_SPECTRUM_NOT_ZERO:
            return (z_data != 0).all()
        elif self.operation == OPERATION_NOT_OUTLIER:
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
            json_dict["criteria_list"] = [criteria.to_dict() for criteria in self.criteria_list]
        return json_dict
        
    def __str__(self):
        return str(self.to_dict())
        
    def check(self, happy_data, x, y):
        return all(criteria.check(happy_data, x, y) for criteria in self.criteria_list)
     
    def get_keys(self):
        return [c.key for c in self.criteria_list]

    def add_criteria(self, criteria):
        self.criteria_list.append(criteria)
        
    def __iter__(self):
        return iter(self.criteria_list)
