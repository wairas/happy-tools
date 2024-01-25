import numpy as np

from typing import Optional, Dict, Tuple

from ._preprocessor import Preprocessor


class PassThroughPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pass-through"

    def description(self) -> str:
        return "Dummy, just passes through the data"

    def _do_apply(self, data: np.ndarray, metadata: Optional[Dict] = None) -> Tuple[np.ndarray, Optional[Dict]]:
        return data, metadata
