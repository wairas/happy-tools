import argparse

import spectral.io.envi as envi
from ._preprocessor import Preprocessor


class WhiteReferencePreprocessor(Preprocessor):

    def name(self) -> str:
        return "white-ref"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-f", "--white_reference_file", type=str, help="TODO", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["white_reference_file"] = ns.white_reference_file

    def _do_apply(self, data, metadata=None):
        white_reference = self.params.get('white_reference', None)
        white_reference_file = None
        if white_reference is None:
            white_reference_file = self.params.get('white_reference_file', None)
        if white_reference_file is not None:
            ref = envi.open(white_reference_file)
            white_reference = ref.load()
        if white_reference is not None:
            # Apply white reference correction by dividing the data by the provided white reference
            corrected_data = data / white_reference
            return corrected_data, metadata
        else:
            return data, metadata
