import unittest

from typing import List

from happy.preprocessors import Preprocessor, SNVPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class SNVPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return [SNVPreprocessor()]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(SNVPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
