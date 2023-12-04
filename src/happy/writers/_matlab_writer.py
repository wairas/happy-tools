import argparse
import numpy as np
import os
from happy.data import HappyData
from ._happydata_writer import HappyDataWriter
import scipy.io as sio


PH_BASEDIR = "{BASEDIR}"
PH_SAMPLEID = "{SAMPLEID}"
PH_REPEAT = "{REPEAT}"

DEFAULT_OUTPUT = PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".mat"


class MatlabWriter(HappyDataWriter):

    def __init__(self, base_dir=None):
        super().__init__(base_dir=base_dir)
        self._output_format = DEFAULT_OUTPUT

    def name(self) -> str:
        return "matlab-writer"

    def description(self) -> str:
        return "Writes data in Matlab format."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-o", "--output", type=str, help="The pattern for the output files.", default=DEFAULT_OUTPUT, required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._output_format = ns.output_format

    def _write_item(self, happy_data, datatype_mapping=None):
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id
        os.makedirs(self.base_dir, exist_ok=True)
        filepath = self._output_format.replace(PH_BASEDIR, self.base_dir).replace(PH_SAMPLEID, sample_id).replace(PH_REPEAT, region_id)
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

