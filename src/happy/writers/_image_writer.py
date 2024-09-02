import argparse
import json
import os
from typing import Tuple, Optional

from happy.data import HappyData, DataManager
from happy.data.normalization import SimpleNormalization
from ._happydata_writer import HappyDataWriterWithOutputPattern, HappyDataWriterWithNormalization, PH_BASEDIR, PH_SAMPLEID, PH_REPEAT


class ImageWriter(HappyDataWriterWithOutputPattern, HappyDataWriterWithNormalization):

    def __init__(self, base_dir: str = "."):
        super().__init__(base_dir=base_dir)
        self._width = 0
        self._height = 0
        self._red_channel = 0
        self._green_channel = 0
        self._blue_channel = 0
        self._normalization = None
        self._suppress_metadata = False

    def name(self) -> str:
        return "image-writer"

    def description(self) -> str:
        return "Generates images from the data. The type of image is determined by the extension of the output files pattern."

    def update_extension(self, ext: str):
        """
        Uses the new image extension, e.g., .png or .jpg.

        :param ext: the extension to use (incl dot).
        :type ext: str
        """
        self._output = os.path.splitext(self._output)[0] + ext

    def _get_default_output(self):
        return PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".png"

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-R", "--red_channel", metavar="INT", help="The wave length to use for the red channel", default=0, type=int, required=False)
        parser.add_argument("-G", "--green_channel", metavar="INT", help="The wave length to use for the green channel", default=0, type=int, required=False)
        parser.add_argument("-B", "--blue_channel", metavar="INT", help="The wave length to use for the blue channel", default=0, type=int, required=False)
        parser.add_argument("-W", "--width", metavar="INT", help="The custom width to use for the image; <=0 for the default", default=0, type=int, required=False)
        parser.add_argument("-H", "--height", metavar="INT", help="The custom height to use for the image; <=0 for the default", default=0, type=int, required=False)
        parser.add_argument("-N", "--normalization", metavar="PLUGIN", help="The normalization plugin and its options to use", default=SimpleNormalization().name(), type=str, required=False)
        parser.add_argument("--suppress_metadata", action="store_true", help="Whether to suppress the output of the meta-data", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._red_channel = ns.red_channel
        self._green_channel = ns.green_channel
        self._blue_channel = ns.blue_channel
        self._width = ns.width
        self._height = ns.height
        self._normalization = ns.normalization
        self._suppress_metadata = ns.suppress_metadata

    def rgb(self, rgb: Tuple[int, int, int]):
        """
        Sets the RGB values to use.

        :param rgb: the 3-tuple of the red, green, blue channels to use
        :type rgb: tuple
        """
        self._red_channel = rgb[0]
        self._green_channel = rgb[1]
        self._blue_channel = rgb[2]

    def normalization(self, norm: Optional[str]):
        """
        Sets the normalization method to use.

        :param norm: the commandline of the normalization plugin
        :type norm: str or None
        """
        self._normalization = norm

    def _write_item(self, happy_data, datatype_mapping=None):
        def log(msg):
            self.logger().info(msg)
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id
        self.logger().info("Creating dir: %s" % self.base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        # output image
        path_png = self._expand_output(self._output, sample_id, region_id)
        self.logger().info("Writing: %s" % path_png)
        datamanager = DataManager(log_method=log)
        datamanager.scan_data = happy_data.data
        datamanager.set_normalization(self._normalization)
        datamanager.reset_norm_data()
        datamanager.output_image(self._red_channel, self._green_channel, self._blue_channel, path_png, width=self._width, height=self._height)
        if not self._suppress_metadata:
            # output meta-data
            path_meta = os.path.splitext(path_png)[0] + "-meta.json"
            self.logger().info("Writing: %s" % path_png)
            with open(path_meta, "w") as fp:
                json.dump(happy_data.global_dict, fp, indent=2)

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping=datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_item(happy_data_or_list)
