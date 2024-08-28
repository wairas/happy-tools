import abc
import argparse
from happy.base.core import PluginWithLogging
from happy.data import HappyData

from typing import List


class HappyDataReader(PluginWithLogging, abc.ABC):

    def __init__(self, base_dir: str = None):
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

    def _get_sample_ids(self) -> List[str]:
        raise NotImplementedError()

    def get_sample_ids(self) -> List[str]:
        if not self._initialized:
            self._initialize()
        return self._get_sample_ids()

    def _load_data(self, sample_id: str) -> List[HappyData]:
        raise NotImplementedError()

    def load_data(self, sample_id: str) -> List[HappyData]:
        if not self._initialized:
            self._initialize()
        return self._load_data(sample_id)

    def _load_region(self, sample_id: str, region_name: str) -> HappyData:
        raise NotImplementedError()

    def load_region(self, sample_id: str, region_name: str) -> HappyData:
        if not self._initialized:
            self._initialize()
        return self._load_region(sample_id, region_name)
