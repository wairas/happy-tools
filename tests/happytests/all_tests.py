import unittest

import happytests.criteria.all_tests
import happytests.readers.all_tests
import happytests.region_extractors.all_tests
import happytests.preprocessors.all_tests


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    result = unittest.TestSuite()
    result.addTests(happytests.criteria.all_tests.suite())
    result.addTests(happytests.readers.all_tests.suite())
    result.addTests(happytests.region_extractors.all_tests.suite())
    result.addTests(happytests.preprocessors.all_tests.suite())
    return result


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
