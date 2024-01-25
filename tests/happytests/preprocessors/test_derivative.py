import unittest

from typing import List

from happy.preprocessors import Preprocessor, DerivativePreprocessor
from happytests.preprocessors import PreprocessorTestCase


class DerivativePreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = DerivativePreprocessor()
        pp2 = DerivativePreprocessor()
        pp2.parse_args(["-d", "0"])
        pp3 = DerivativePreprocessor()
        pp3.parse_args(["-w", "5", "-d", "2", "-p", "3"])
        return [pp1, pp2, pp3]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(DerivativePreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
