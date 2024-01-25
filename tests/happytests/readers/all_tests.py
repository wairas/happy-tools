import unittest

import happytests.readers.test_happyreader
import happytests.readers.test_matlabreader


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    result = unittest.TestSuite()
    result.addTests(happytests.readers.test_happyreader.suite())
    result.addTests(happytests.readers.test_matlabreader.suite())
    return result


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
