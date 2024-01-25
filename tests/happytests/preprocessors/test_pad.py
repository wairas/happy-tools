import unittest

from typing import List

from happy.preprocessors import Preprocessor, PadPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class PadPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = PadPreprocessor()
        pp2 = PadPreprocessor()
        pp2.parse_args(["-W", "150", "-H", "150", "-v", "1"])
        return [pp1, pp2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(PadPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
