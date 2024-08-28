import argparse
import os
import re
from ._happydata_reader import HappyDataReader
from happy.readers.spectra import EnviReader
from happy.data import HappyData

from typing import List, Optional

DEFAULT_ENVI_EXT = ".hdr"


class EnviHappyDataReader(HappyDataReader):

    def __init__(self, base_dir: str = None, extension: str = DEFAULT_ENVI_EXT, exclude: Optional[List[str]] = None):
        super().__init__(base_dir=base_dir)
        self.extension = extension
        self.exclude = exclude

    def name(self) -> str:
        return "envi-reader"

    def description(self) -> str:
        return "Reads data in ENVI format."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-e", "--extension", metavar="EXT", type=str, help="The file extension to look for (incl dot), e.g., '.hdr'.", required=False, default=DEFAULT_ENVI_EXT)
        parser.add_argument("--exclude", metavar="REGEXP", type=str, help="The optional regular expression(s) for excluding ENVI files to read (gets applied to file name, not path).", required=False, nargs="*")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.extension = ns.extension
        self.exclude = ns.exclude

    def _get_sample_ids(self) -> List[str]:
        sample_ids = []
        for sample_id in os.listdir(self.base_dir):
            sample_path = os.path.join(self.base_dir, sample_id)
            if sample_id.endswith(self.extension) and os.path.isfile(sample_path):
                add = True
                if self.exclude is not None:
                    for ext in self.exclude:
                        if re.search(ext, sample_id) is not None:
                            add = False
                            break
                if add:
                    sample_ids.append(sample_id)
        sample_ids = sorted(sample_ids)
        return sample_ids

    def _load_data(self, sample_id: str) -> List[HappyData]:
        sample_id = os.path.splitext(sample_id)[0]
        region_id = ""
        return [self.load_region(sample_id, region_id)]

    def _load_region(self, sample_id: str, region_name: str) -> HappyData:
        def filename_func(base_dir, sample_id):
            return os.path.join(base_dir, sample_id + self.extension)

        hyperspec_file_path = os.path.join(self.base_dir, sample_id + region_name + self.extension)
        self.logger().info(f"{sample_id}{region_name}{self.extension}")

        if not os.path.exists(hyperspec_file_path):
            raise ValueError(f"Hyperspectral ENVI file not found for sample_id: {sample_id}")

        envi_reader = EnviReader(self.base_dir, filename_func=filename_func)
        envi_reader.load_data(sample_id)
        hyperspec_data = envi_reader.get_numpy()

        # Create HappyData object for this region
        # TODO any meta-data?
        happy_data = HappyData(sample_id, region_name, hyperspec_data, dict(), dict(), wavenumbers=envi_reader.wavelengths)

        return happy_data
