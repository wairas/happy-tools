import unittest

from typing import List, Tuple

from ._happydatareader_testcase import HappyDataReaderTestCase
from happy.readers import HappyDataReader, HappyReader


class HappyReaderTest(HappyDataReaderTestCase):

    def _regression_setup(self) -> List[HappyDataReader]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return [HappyReader()]

    def _regression_data(self) -> List[Tuple[str, str]]:
        """
        Returns the data to use for the regression test.

        :return: the base dir/sample ID tuples to read
        :rtype: list
        """
        return [(self._data_dir(), "92AV3C")]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(HappyReaderTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
