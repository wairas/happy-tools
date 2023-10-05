import numpy as np


class PredictionActualHandler:
    @classmethod
    def to_list(cls, data, remove_last_dim=True, one_hot=False, num_classes=None):
        if data is None:
            return None
        
        if isinstance(data, list):
            if remove_last_dim:
                data = [np.squeeze(item) if item.shape[-1] == 1 else item for item in data]
            if not one_hot:
                return data
            else:
                return [cls.to_one_hot(item, num_classes) if not cls.is_one_hot_encoded(item) else item for item in data]
        else:
            if remove_last_dim and data.shape[-1] == 1:
                data = np.squeeze(data)
            if not one_hot:
                return [data]
            else:
                if cls.is_one_hot_encoded(data):
                    return [data]
                else:
                    return [cls.to_one_hot(data, num_classes)]
    
    @staticmethod
    def to_one_hot(data, num_classes):
        unique_values = np.unique(data)
        if num_classes is None:
            num_classes = len(unique_values)
        return np.eye(num_classes)[data]

    @staticmethod
    def is_one_hot_encoded(data):
        return np.all(data.sum(axis=-1) == 1)

    @classmethod
    def to_array(cls, data, remove_last_dim=True):
        if isinstance(data, list):
            return np.array([np.squeeze(item) if remove_last_dim and item.shape[-1] == 1 else item for item in data])
        else:
            return np.squeeze(data) if remove_last_dim and data.shape[-1] == 1 else data
