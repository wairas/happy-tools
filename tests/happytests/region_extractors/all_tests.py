import unittest

import happytests.region_extractors.test_full_region_extractor
import happytests.region_extractors.test_grid_region_extractor


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    result = unittest.TestSuite()
    result.addTests(happytests.region_extractors.test_full_region_extractor.suite())
    result.addTests(happytests.region_extractors.test_grid_region_extractor.suite())
    return result


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
