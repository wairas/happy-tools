import unittest

from typing import List

from happy.preprocessors import Preprocessor, CropPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class CropPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = CropPreprocessor()
        pp1.parse_args(["-x", "10", "-y", "10", "-W", "75", "-H", "50"])
        pp2 = CropPreprocessor()
        pp2.parse_args(["-x", "10", "-y", "10", "-W", "75", "-H", "50", "-p"])
        return [pp1, pp2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(CropPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
