import unittest

from typing import List

from happy.preprocessors import Preprocessor, DownsamplePreprocessor
from happytests.preprocessors import PreprocessorTestCase


class DownsamplePreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = DownsamplePreprocessor()
        pp2 = DownsamplePreprocessor()
        pp2.parse_args(["-x", "1", "-y", "3"])
        return [pp1, pp2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(DownsamplePreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
