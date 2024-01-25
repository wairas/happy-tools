import unittest

import happytests.criteria.test_criteria


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    result = unittest.TestSuite()
    result.addTests(happytests.criteria.test_criteria.suite())
    return result


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
