from sklearn.preprocessing import StandardScaler
from ._preprocessor import Preprocessor


class StandardScalerPreprocessor(Preprocessor):

    def name(self) -> str:
        return "std-scaler"

    def description(self) -> str:
        return "TODO"

    def _do_apply(self, data, metadata=None):
        scaler = StandardScaler()
        reshaped_data = data.reshape(-1, data.shape[-1])  # Flatten the data along the last dimension
        scaled_data = scaler.fit_transform(reshaped_data)
        scaled_data = scaled_data.reshape(data.shape)  # Reshape back to the original shape
        return scaled_data, metadata
