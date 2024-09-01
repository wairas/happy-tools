import abc
import argparse
from happy.base.core import PluginWithLogging
from happy.data import HappyData


PH_BASEDIR = "{BASEDIR}"
PH_SAMPLEID = "{SAMPLEID}"
PH_REPEAT = "{REPEAT}"
PH_REGION = "{REGION}"
PLACEHOLDERS_OUTPUT = [
    PH_BASEDIR,
    PH_SAMPLEID,
    PH_REPEAT,
    PH_REGION,
]


def output_pattern_help():
    """
    Outputs a help string to be used in the options, listing the available placeholders
    for the output pattern.

    :return: the pattern help string
    :rtype: str
    """
    return "The following placeholders are available for the output pattern: %s" % ", ".join(PLACEHOLDERS_OUTPUT)


class HappyDataWriter(PluginWithLogging, abc.ABC):

    def __init__(self, base_dir=None):
        super().__init__()
        self.base_dir = base_dir
        self._initialized = False

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-b", "--base_dir", type=str, help="The base directory for the data", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._initialized = False
        self.base_dir = ns.base_dir

    def _initialize(self):
        self._initialized = True

    def update_base_dir(self, base_dir: str):
        """
        Sets the new base directory to use. Unsets the initialized state.

        :param base_dir: the new base directory
        :type base_dir: str
        """
        self.base_dir = base_dir
        self._initialized = False

    def _expand_output(self, output, sample_id, region_id):
        result = output.replace(PH_BASEDIR, self.base_dir)
        result = result.replace(PH_SAMPLEID, sample_id)
        result = result.replace(PH_REPEAT, region_id)
        result = result.replace(PH_REGION, region_id)
        return result

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        raise NotImplementedError()

    def _check_data(self, happy_data_or_list):
        if isinstance(happy_data_or_list, list):
            return None
        elif isinstance(happy_data_or_list, HappyData):
            return None
        else:
            return "Input should be either a HappyData object or a list of HappyData objects."

    def write_data(self, happy_data_or_list, datatype_mapping=None):
        if not self._initialized:
            self._initialize()

        msg = self._check_data(happy_data_or_list)
        if msg is not None:
            raise ValueError(msg)

        self._write_data(happy_data_or_list, datatype_mapping=datatype_mapping)
