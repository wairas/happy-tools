import argparse
import copy
from happy.base.registry import REGISTRY
from happy.preprocessors import Preprocessor
from seppl import split_cmdline, split_args


class MultiPreprocessor(Preprocessor):

    def name(self) -> str:
        return "multi"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-p", "--preprocessors", type=str, help="TODO", required=False, nargs="*")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        preprocessor_list = []
        all = REGISTRY.preprocessors()
        for preprocessor in ns.preprocessors:
            plugins = split_args(split_cmdline(preprocessor), all.keys())
            for key in plugins:
                if key == "":
                    continue
                name = all[key][0]
                plugin = copy.deepcopy(all[name])
                plugin.parse_args(plugins[key][1:])
                preprocessor_list.append(plugin)
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
