import abc
import os
import unittest


class HappyTestCase(unittest.TestCase, abc.ABC):

    def _data_dir(self) -> str:
        """
        Returns the directory with the test data.

        :return: the directory
        :rtype: str
        """
        result = os.path.dirname(__file__)
        result = os.path.dirname(result)
        result = os.path.join(result, "testdata")
        return result
