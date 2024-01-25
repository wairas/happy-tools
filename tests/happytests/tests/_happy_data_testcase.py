import abc

from typing import List

from ._test_data import init_92AV3C
from ._happy_regression_testcase import HappyRegressionTestCase
from happy.data import HappyData
from happy.readers import HappyReader


class HappyDataTestCase(HappyRegressionTestCase, abc.ABC):

    def load_92AV3C(self) -> List[HappyData]:
        """
        Loads and returns the 92AV3C dataset.

        :return: the 92AV3C dataset in happy format (as list)
        :rtype: list
        """
        init_92AV3C(self._data_dir())
        reader = HappyReader(base_dir=self._data_dir())
        return reader.load_data("92AV3C")

    def setUp(self):
        super().setUp()
        self.data_92AV3C = self.load_92AV3C()
