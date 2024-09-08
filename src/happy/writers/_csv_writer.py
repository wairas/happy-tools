import argparse
import csv
import json
import os

import numpy as np

from happy.data import HappyData
from ._happydata_writer import HappyDataWriterWithOutputPattern, PH_BASEDIR, PH_SAMPLEID, PH_REPEAT, PH_REGION

DEFAULT_WAVE_NUMBER_PREFIX = "wave-"


class CSVWriter(HappyDataWriterWithOutputPattern):

    def __init__(self, base_dir: str = "."):
        super().__init__(base_dir=base_dir)
        self._wave_number_prefix = DEFAULT_WAVE_NUMBER_PREFIX
        self._output_wave_number_index = False
        self._suppress_metadata = False
        self._combine_repeats = False

    def name(self) -> str:
        return "csv-writer"

    def description(self) -> str:
        return "Generates CSV spreadsheets with spectra from the data. When omitting the repeat/region " \
            + "pattern from the output pattern, the CSV files get combined and meta-data output is " \
            + "automatically suppressed."

    def _get_default_output(self):
        return PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".csv"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-w", "--wave_number_prefix", type=str, help="The prefix to use for the spectral columns", default=DEFAULT_WAVE_NUMBER_PREFIX, required=False)
        parser.add_argument("-i", "--output_wave_number_index", action="store_true", help="Whether to output the index of the wave number instead of the wave length", required=False)
        parser.add_argument("--suppress_metadata", action="store_true", help="Whether to suppress the output of the meta-data", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._wave_number_prefix = ns.wave_number_prefix
        self._output_wave_number_index = ns.output_wave_number_index
        self._suppress_metadata = ns.suppress_metadata

    def _initialize(self):
        super()._initialize()
        if (PH_REPEAT not in self._output) and (PH_REGION not in self._output):
            self._combine_repeats = True
            if not self._suppress_metadata:
                self.logger().warning("Repeat/region pattern " + PH_REPEAT + "/" + PH_REGION + " not in output pattern, suppressing output of meta-data!")
                self._suppress_metadata = True

    def _write_item(self, happy_data, datatype_mapping=None):
        rows, cols, bands = happy_data.data.shape
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id
        if not os.path.exists(self.base_dir):
            self.logger().info("Creating dir: %s" % self.base_dir)
            os.makedirs(self.base_dir, exist_ok=True)

        # output spreadsheet
        path_csv = self._expand_output(self._output, sample_id, region_id)
        append = self._combine_repeats and os.path.exists(path_csv)
        if append:
            self.logger().info("Appending: %s" % path_csv)
            open_flag = "a"
        else:
            self.logger().info("Writing: %s" % path_csv)
            open_flag = "w"

        with open(path_csv, open_flag) as fp:
            writer = csv.writer(fp)

            # header
            if not append:
                row = ["sample_id", "region_id""x", "y"]
                if (happy_data.wavenumbers is None) or self._output_wave_number_index:
                    row.extend([self._wave_number_prefix + str(x) for x in range(bands)])
                else:
                    row.extend([self._wave_number_prefix + str(x) for x in happy_data.wavenumbers])
                writer.writerow(row)

            # data
            for r in range(rows):
                for c in range(cols):
                    row = [happy_data.sample_id, happy_data.region_id, c, r]
                    row.extend(np.squeeze(happy_data.get_spectrum(c, r)))
                    writer.writerow(row)

        # output meta-data
        if not self._suppress_metadata:
            path_meta = os.path.splitext(path_csv)[0] + "-meta.json"
            self.logger().info("Writing: %s" % path_csv)
            with open(path_meta, "w") as fp:
                json.dump(happy_data.global_dict, fp, indent=2)

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping=datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_item(happy_data_or_list)
