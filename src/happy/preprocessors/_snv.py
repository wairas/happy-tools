import numpy as np

from typing import Optional, Dict, Tuple

from ._preprocessor import Preprocessor


class SNVPreprocessor(Preprocessor):

    def name(self) -> str:
        return "snv"

    def description(self) -> str:
        return "Standard normal variate"

    def _do_apply(self, data: np.ndarray, metadata: Optional[Dict] = None) -> Tuple[np.ndarray, Optional[Dict]]:
        mean = np.mean(data, axis=2, keepdims=True)
        std = np.std(data, axis=2, keepdims=True)
        normalized_data = (data - mean) / std
        return normalized_data, metadata
