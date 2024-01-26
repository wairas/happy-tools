import argparse

from typing import List

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

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        happy_data_list = [happy_data]
        for preprocessor in self.params.get('preprocessor_list', []):
            tmp_list = []
            for item in happy_data_list:
                preprocessor.fit(item)
                new_happy_data_list = preprocessor.apply(item)
                tmp_list.extend(new_happy_data_list)
            happy_data_list = tmp_list
        return happy_data_list

    def to_string(self) -> str:
        preprocessor_strings = [preprocessor.to_string() for preprocessor in self.params.get('preprocessor_list', [])]
        return " -> ".join(preprocessor_strings)
