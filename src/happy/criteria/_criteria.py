import re
import numpy as np

from happy.base.core import ConfigurableObject


OP_NOT_MISSING = "not_missing"
OP_EQUALS = "equals"
OP_GREATER_THAN = "greater_than"
OP_NOT_IN = "not_in"
OP_IN = "in"
OP_MATCHES = "matches"
OP_SPECTRUM_NOT_ZERO = "spectrum_not_zero"
OP_NOT_OUTLIER = "not_outlier"
OPERATIONS = [
    OP_NOT_MISSING,
    OP_EQUALS,
    OP_GREATER_THAN,
    OP_NOT_IN,
    OP_IN,
    OP_MATCHES,
    OP_SPECTRUM_NOT_ZERO,
    OP_NOT_OUTLIER,
]


class Criteria(ConfigurableObject):
    def __init__(self, operation=None, value=None, key=None):
        if (operation is not None) and (operation not in OPERATIONS):
            raise Exception("Unknown operation: %s" % operation)
        self.operation = operation
        self.value = value
        self.key = key

    def to_dict(self):
        result = super().to_dict()
        result.update({
            'operation': self.operation,
            'value': self.value,
            'key': self.key
        })
        return result

    def from_dict(self, d):
        self.operation = d["operation"]
        self.value = d["value"]
        self.key = d["key"]
        return self

    def __str__(self):
        return str(self.to_dict())
        
    def get_keys(self):
        return [self.key]

    def check(self, happy_data, x, y):
        z_data = happy_data.get_spectrum(x, y)
        if z_data is None:
            return False
        value = happy_data.get_meta_data(x=x, y=y, key=self.key)
        if self.operation == OP_NOT_MISSING:
            return value is not None
        if self.operation == OP_EQUALS:
            return value == self.value
        elif self.operation == OP_GREATER_THAN:
            return value > self.value
        elif self.operation == OP_NOT_IN:
            return value not in self.value
        elif self.operation == OP_IN:
            return value in self.value
        elif self.operation == OP_MATCHES:
            return bool(re.search(self.value, value))
        elif self.operation == OP_SPECTRUM_NOT_ZERO:
            return (z_data != 0).all()
        elif self.operation == OP_NOT_OUTLIER:
            z_data_mean = np.mean(z_data)
            z_data_std = np.std(z_data)
            return np.abs(z_data - z_data_mean) <= 2 * z_data_std
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")


class CriteriaGroup(ConfigurableObject):
    def __init__(self, criteria_list=None):
        self.criteria_list = criteria_list or []

    def to_dict(self):
        result = super().to_dict()
        if self.criteria_list:
            result["criteria_list"] = [criteria.to_dict() for criteria in self.criteria_list]
        return result

    def from_dict(self, d):
        self.criteria_list = []
        if "criteria_list" in d:
            for dc in d["criteria_list"]:
                c = Criteria.create_from_dict(dc)
                self.criteria_list.append(c)
        return self

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
