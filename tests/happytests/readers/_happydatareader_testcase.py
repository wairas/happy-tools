import abc
import copy
from typing import List, Tuple

from happy.readers import HappyDataReader
from happytests.tests import HappyRegressionTestCase, init_92AV3C


class HappyDataReaderTestCase(HappyRegressionTestCase, abc.ABC):

    def setUp(self):
        super().setUp()
        init_92AV3C(self._data_dir())

    def _regression_setup(self) -> List[HappyDataReader]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return []

    def _regression_data(self) -> List[Tuple[str, str]]:
        """
        Returns the data to use for the regression test.

        :return: the base dir/sample ID tuples to read
        :rtype: list
        """
        return []

    def _regression_item_to_str(self, item) -> str:
        """
        Turns the regression item into a string.

        :param item: the regression item to convert to a string
        :return: the generated string
        :rtype: str
        """
        return repr(item.data.shape) + "\n\n" + repr(item.data)

    def test_regression(self):
        """
        Performs the regression test.
        """
        self._init_regression_dir()
        readers = self._regression_setup()
        if len(readers) == 0:
            return
        data = self._regression_data()
        read_data = []
        for reader in readers:
            r = copy.deepcopy(reader)
            for base_dir, sample_id in data:
                r.base_dir = base_dir
                d = r.load_data(sample_id)
                read_data.extend(d)
        regression_data = []
        for item in read_data:
            regression_data.append(self._regression_item_to_str(item))
        self._compare_regression("\n".join(regression_data))
