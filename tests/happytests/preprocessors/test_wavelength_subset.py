import unittest

from typing import List

from happy.preprocessors import Preprocessor, WavelengthSubsetPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class WavelengthSubsetPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = WavelengthSubsetPreprocessor()
        pp2 = WavelengthSubsetPreprocessor()
        pp2.parse_args(["-s", "3", "4", "5", "10", "11", "12"])
        return [pp1, pp2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(WavelengthSubsetPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
