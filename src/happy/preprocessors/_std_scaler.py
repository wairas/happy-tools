from sklearn.preprocessing import StandardScaler
from ._preprocessor import Preprocessor
from happy.data import HappyData


class StandardScalerPreprocessor(Preprocessor):

    def name(self) -> str:
        return "std-scaler"

    def description(self) -> str:
        return "Standardize features by removing the mean and scaling to unit variance."

    def _do_apply(self, happy_data: HappyData) -> HappyData:
        scaler = StandardScaler()
        reshaped_data = happy_data.data.reshape(-1, happy_data.data.shape[-1])  # Flatten the data along the last dimension
        scaled_data = scaler.fit_transform(reshaped_data)
        scaled_data = scaled_data.reshape(happy_data.data.shape)  # Reshape back to the original shape
        return happy_data.copy(data=scaled_data)
