import argparse
import json
import os
import spectral.io.envi as envi

from happy.data import HappyData
from ._happydata_writer import HappyDataWriter, PH_BASEDIR, PH_SAMPLEID, PH_REPEAT, output_pattern_help


DEFAULT_OUTPUT = PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".hdr"


class EnviWriter(HappyDataWriter):

    def __init__(self, base_dir=None):
        super().__init__(base_dir=base_dir)
        self._output = DEFAULT_OUTPUT

    def name(self) -> str:
        return "envi-writer"

    def description(self) -> str:
        return "Exports the data in ENVI format and the meta-data as JSON alongside."

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
        path_envi = self._expand_output(self._output, sample_id, region_id)
        path_meta = os.path.splitext(path_envi)[0] + "-meta.json"
        self.logger().info("Writing: %s" % path_envi)
        envi.save_image(path_envi, happy_data.data, force=True)
        self.logger().info("Saving meta-data to: %s" % path_meta)
        with open(path_meta, "w") as fp:
            json.dump(happy_data.metadata_dict, fp, indent=2)

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping=datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_item(happy_data_or_list)
