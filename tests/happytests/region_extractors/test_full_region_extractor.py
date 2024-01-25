import unittest

from typing import List

from happy.region_extractors import RegionExtractor, FullRegionExtractor
from happytests.region_extractors import RegionExtractorTestCase


class FullRegionExtractorTest(RegionExtractorTestCase):

    def _regression_setup(self) -> List[RegionExtractor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return [FullRegionExtractor()]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(FullRegionExtractorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
