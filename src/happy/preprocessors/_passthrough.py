from ._preprocessor import Preprocessor


class PassThrough(Preprocessor):

    def name(self) -> str:
        return "pass-through"

    def description(self) -> str:
        return "Dummy, just passes through the data"

    def _do_apply(self, data, metadata=None):
        # Apply Standard Normal Variate (SNV) correction along the wavelength dimension
        return data, metadata
