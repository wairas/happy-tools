import unittest

from typing import List

from happy.preprocessors import Preprocessor, PassThroughPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class PassThroughPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return [PassThroughPreprocessor()]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(PassThroughPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
