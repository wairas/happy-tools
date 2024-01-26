from ._preprocessor import Preprocessor
from happy.data import HappyData


class PassThroughPreprocessor(Preprocessor):

    def name(self) -> str:
        return "pass-through"

    def description(self) -> str:
        return "Dummy, just passes through the data"

    def _do_apply(self, happy_data: HappyData) -> HappyData:
        return happy_data
