import argparse

from ._preprocessor import Preprocessor
from happy.data.white_ref import AbstractWhiteReferenceMethod


class WhiteReferencePreprocessor(Preprocessor):

    def name(self) -> str:
        return "white-ref"

    def description(self) -> str:
        return "Applies the specified white reference method to the data."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-m", "--method", type=str, help="The white reference method to apply", default="wr-none", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["method"] = AbstractWhiteReferenceMethod.parse_method(ns.method)

    def _do_apply(self, data, metadata=None):
        method = self.params.get('method', None)
        if method is None:
            return data, metadata
        else:
            return method.apply(data), metadata
