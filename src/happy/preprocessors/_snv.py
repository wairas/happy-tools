import numpy as np

from typing import List

from ._preprocessor import Preprocessor
from happy.data import HappyData


class SNVPreprocessor(Preprocessor):

    def name(self) -> str:
        return "snv"

    def description(self) -> str:
        return "Standard normal variate"

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        mean = np.mean(happy_data.data, axis=2, keepdims=True)
        std = np.std(happy_data.data, axis=2, keepdims=True)
        normalized_data = (happy_data.data - mean) / std
        return [happy_data.copy(data=normalized_data)]
