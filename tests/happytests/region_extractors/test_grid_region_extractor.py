import unittest

from typing import List

from happy.region_extractors import RegionExtractor, GridRegionExtractor
from happytests.region_extractors import RegionExtractorTestCase


class GridRegionExtractorTest(RegionExtractorTestCase):

    def _regression_setup(self) -> List[RegionExtractor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        ex1 = GridRegionExtractor()
        ex1.parse_args(["-r", "75", "50"])
        ex2 = GridRegionExtractor()
        ex2.parse_args(["-r", "75", "50", "-T"])
        return [ex1, ex2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(GridRegionExtractorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
