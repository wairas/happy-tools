import abc
import argparse
from typing import Optional
from seppl import split_args, split_cmdline, args_to_objects
from happy.base.registry import REGISTRY
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

    def __init__(self, base_dir: str = "."):
        super().__init__()
        self.base_dir = base_dir
        self._initialized = False

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-b", "--base_dir", type=str, help="The base directory for the data", required=False, default=".")
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

    @classmethod
    def parse_writer(cls, cmdline: str) -> Optional['HappyDataWriter']:
        """
        Splits the command-line, parses the arguments, instantiates and returns the writer.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the writer, None if not exactly one selector parsed
        :rtype: HappyDataWriter
        """
        plugins = REGISTRY.happydata_writers()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        l = args_to_objects(args, plugins, allow_global_options=False)
        if len(l) == 1:
            return l[0]
        else:
            return None


class HappyDataWriterWithOutputPattern(HappyDataWriter, abc.ABC):
    """
    Writers that support custom output patterns.
    """

    def __init__(self, base_dir: str = "."):
        super().__init__(base_dir=base_dir)
        self._output = self._get_default_output()

    def _get_default_output(self):
        raise NotImplementedError()

    def _output_help(self):
        return "The pattern for the output files; " + output_pattern_help()

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-o", "--output", type=str, help=self._output_help(), default=self._get_default_output(), required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self._output = ns.output

    def _expand_output(self, output, sample_id, region_id):
        result = output.replace(PH_BASEDIR, self.base_dir)
        result = result.replace(PH_SAMPLEID, sample_id)
        result = result.replace(PH_REPEAT, region_id)
        result = result.replace(PH_REGION, region_id)
        return result

    def update_output(self, output: str):
        """
        For updating the output pattern programmatically.

        :param output: the new output pattern
        :type output: str
        """
        self._output = output


class HappyDataWriterWithNormalization:
    """
    Mixing for writers that support normalization.
    """

    def normalization(self, norm: Optional[str]):
        """
        Sets the normalization method to use.

        :param norm: the commandline of the normalization plugin
        :type norm: str or None
        """
        raise NotImplementedError()
