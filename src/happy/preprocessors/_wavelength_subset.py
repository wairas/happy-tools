import argparse

from ._preprocessor import Preprocessor


class WavelengthSubsetPreprocessor(Preprocessor):

    def name(self) -> str:
        return "wavelength-subset"

    def description(self) -> str:
        return "TODO"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-s", "--subset_indices", type=int, help="The explicit 0-based wavelength indices to use", required=False, nargs="+")
        parser.add_argument("-f", "--from_index", type=int, help="The first 0-based wavelength to include", required=False, default=60)
        parser.add_argument("-t", "--to_index", type=int, help="The last 0-based wavelength to include", required=False, default=189)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["subset_indices"] = ns.subset_indices
        self.params["from_index"] = ns.from_index
        self.params["to_index"] = ns.to_index

    def _do_apply(self, data, metadata=None):
        subset_indices = self.params.get('subset_indices', None)
        from_index = self.params.get('from_index', None)
        to_index = self.params.get('to_index', None)
        if subset_indices is None:
            if (from_index is not None) and (to_index is not None):
                subset_indices = list(range(from_index, to_index + 1))
        if subset_indices is not None:
            # Select the subset of wavelengths from the data
            subset_data = data[:, :, subset_indices]
            return subset_data, metadata
        else:
            return data, metadata
