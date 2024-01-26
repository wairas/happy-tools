import argparse

from happy.preprocessors import Preprocessor
from happy.data import HappyData


class MultiPreprocessor(Preprocessor):

    def name(self) -> str:
        return "multi-pp"

    def description(self) -> str:
        return "Combines multiple pre-processors."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-p", "--preprocessors", type=str, help="The preprocessors to wrap. Either preprocessor command-line(s) or file with one preprocessor command-line per line.", required=False, default=None)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        preprocessor_list = []
        if ns.preprocessors is not None:
            preprocessor_list = Preprocessor.parse_preprocessors(ns.preprocessors)
        self.params["preprocessor_list"] = preprocessor_list

    def _do_apply(self, happy_data: HappyData) -> HappyData:
        for preprocessor in self.params.get('preprocessor_list', []):
            preprocessor.fit(happy_data)
            happy_data = preprocessor.apply(happy_data)
        return happy_data

    def to_string(self) -> str:
        preprocessor_strings = [preprocessor.to_string() for preprocessor in self.params.get('preprocessor_list', [])]
        return " -> ".join(preprocessor_strings)
