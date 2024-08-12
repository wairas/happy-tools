import argparse
import os.path

from typing import List

import spectral.io.envi as envi
from ._preprocessor import Preprocessor
from happy.data import HappyData


class SubtractPreprocessor(Preprocessor):

    def name(self) -> str:
        return "subtract"

    def description(self) -> str:
        return "Subtracts the specified reference."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-f", "--file", metavar="FILE", help="the ENVI file to subtract from the data passing through", default=".", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["file"] = ns.file
        if "data" in self.params:
            del self.params["data"]

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        if "data" not in self.params:
            if self.params["file"] is None:
                raise Exception("No ENVI file supplied for subtracting!")
            if not os.path.exists(self.params["file"]):
                raise Exception("ENVI file to subtract does not exist: %s" % self.params["file"])
            img = envi.open(self.params["file"])
            self.params["data"] = img.load()

        new_data = happy_data.data - self.params["data"]
        return [happy_data.copy(data=new_data)]
