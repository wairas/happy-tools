import argparse

import spectral.io.envi as envi
from ._preprocessor import Preprocessor


class BlackReferencePreprocessor(Preprocessor):

    def name(self) -> str:
        return "black-ref"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-f", "--black_reference_file", type=str, help="TODO", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["black_reference_file"] = ns.black_reference_file

    def _do_apply(self, data, metadata=None):
        black_reference = self.params.get('black_reference', None)
        black_reference_file = None
        if black_reference is None:
            black_reference_file = self.params.get('black_reference_file', None)
        if black_reference_file is not None:
            ref = envi.open(black_reference_file)
            black_reference = ref.load()
        if black_reference is not None:
            # Apply black reference correction by subtracting the provided black reference from the data
            corrected_data = data - black_reference
            return corrected_data, metadata
        else:
            return data, metadata
