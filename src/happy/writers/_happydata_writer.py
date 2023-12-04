import abc
import argparse
from seppl import Plugin
from happy.data import HappyData


class HappyDataWriter(Plugin, abc.ABC):

    def __init__(self, base_dir=None):
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
