import argparse

from happy.preprocessors import Preprocessor


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

    def _initialize(self):
        super()._initialize()
        self.preprocessor_list = self.params.get('preprocessor_list', [])

    def _do_fit(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            preprocessor.fit(data, metadata)
            data, metadata = preprocessor.apply(data, metadata)
        return self

    def _do_apply(self, data, metadata=None):
        for preprocessor in self.preprocessor_list:
            data, metadata = preprocessor.apply(data, metadata)
        return data, metadata

    def to_string(self):
        preprocessor_strings = [preprocessor.to_string() for preprocessor in self.preprocessor_list]
        return " -> ".join(preprocessor_strings)
