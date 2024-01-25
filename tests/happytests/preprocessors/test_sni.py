import unittest

from typing import List

from happy.preprocessors import Preprocessor, SpectralNoiseInterpolator
from happytests.preprocessors import PreprocessorTestCase


class SpectralNoiseInterpolatorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        pp1 = SpectralNoiseInterpolator()
        pp2 = SpectralNoiseInterpolator()
        pp2.parse_args(["-t", "0.9"])
        return [pp1, pp2]


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(SpectralNoiseInterpolatorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
