import argparse
import numpy as np
import os
from happy.data import HappyData
from ._happydata_writer import HappyDataWriter, PH_BASEDIR, PH_SAMPLEID, PH_REPEAT, output_pattern_help
import scipy.io as sio


DEFAULT_OUTPUT = PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".mat"


class MatlabWriter(HappyDataWriter):

    def __init__(self, base_dir=None):
        super().__init__(base_dir=base_dir)
        self._output = DEFAULT_OUTPUT

    def name(self) -> str:
        return "matlab-writer"

    def description(self) -> str:
        return "Writes data in Matlab format."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-o", "--output", type=str, help="The pattern for the output files; " + output_pattern_help(), default=DEFAULT_OUTPUT, required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._output = ns.output

    def _write_item(self, happy_data, datatype_mapping=None):
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id
        self.logger().info("Creating dir: %s" % self.base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        filepath = self._expand_output(self._output, sample_id, region_id)
        self.logger().info("Writing: %s" % filepath)
        save_dic = dict()
        save_dic["normcube"] = happy_data.data
        if happy_data.wavenumbers is not None:
            save_dic["lambda"] = happy_data.wavenumbers
        if "mask" in happy_data.metadata_dict:
            save_dic["FinalMask"] = np.squeeze(happy_data.metadata_dict["mask"]["data"])
        # TODO ceiling?
        # TODO class?
        # TODO y?
        sio.savemat(filepath, save_dic)

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping=datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_item(happy_data_or_list)

