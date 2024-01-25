import unittest

from typing import List

from happy.preprocessors import Preprocessor, PCAPreprocessor
from happytests.preprocessors import PreprocessorTestCase


class PCAPreprocessorTest(PreprocessorTestCase):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        # TODO PCA does not generate reproducible results,
        #      even with when using a fixed int for random_state?
        # pp1 = PCAPreprocessor()
        # pp2 = PCAPreprocessor()
        # pp2.parse_args(["-n", "3", "-p", "50"])
        # return [pp1, pp2]
        return []


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(PCAPreprocessorTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
