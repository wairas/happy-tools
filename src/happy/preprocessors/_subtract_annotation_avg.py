import argparse
import numpy as np

from typing import List

from ._preprocessor import AbstractOPEXAnnotationsBasedPreprocessor
from happy.data import HappyData


class SubtractAnnotationAveragePreprocessor(AbstractOPEXAnnotationsBasedPreprocessor):

    def name(self) -> str:
        return "subtract-annotation-avg"

    def description(self) -> str:
        return "Calculates the average from the specified annotation (uses outer bbox) and subtracts it from the data passing through."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("--label", metavar="LABEL", help="the annotation to use for calculating the average", default=None, required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.params["label"] = ns.label

    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        if self.params["annotations"] is None:
            self.logger().error("No annotations, cannot subtract annotation average!")
            return [happy_data]

        if self.params["label"] is None:
            raise Exception("No label defined!")

        # locate annotation
        bbox = None
        for obj in self.params["annotations"].objects:
            if obj.label == self.params["label"]:
                bbox = obj.bbox
                break
        if bbox is None:
            self.logger().warning("Failed to locate label '%s' in annotations!" % str(self.params["label"]))
            return [happy_data]

        # compute average
        z_list = [happy_data.get_spectrum(x, y) for x in range(bbox.left, bbox.right + 1) for y in range(bbox.top, bbox.bottom + 1)]
        avg = np.mean(z_list, axis=0)
        new_data = happy_data.data - avg
        return [happy_data.copy(data=new_data)]
