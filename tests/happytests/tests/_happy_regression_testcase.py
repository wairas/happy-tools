import abc
import os
import difflib
import inspect

from difflib import SequenceMatcher

from ._happy_testcase import HappyTestCase


class HappyRegressionTestCase(HappyTestCase, abc.ABC):

    def _regression_dir(self) -> str:
        """
        Returns the directory for storing the regression results.

        :return: the directory
        :rtype: str
        """
        return os.path.join(
            os.path.dirname(inspect.getfile(self.__class__)),
            "regression")

    def _init_regression_dir(self):
        """
        Initializes the regression dir if necessary.
        """
        reg_dir = self._regression_dir()
        os.makedirs(reg_dir, exist_ok=True)

    def _regression_file(self, suffix: str = None) -> str:
        """
        Returns the filename for the regression test results.

        :param suffix: optional suffix
        :type suffix: str
        :return: the filename
        :rtype: str
        """
        if suffix is None:
            suffix = ""
        return os.path.join(
            self._regression_dir(),
            self.__class__.__name__ + suffix + ".reg")

    def _regression_item_to_str(self, item) -> str:
        """
        Turns the regression item into a string.

        :param item: the regression item to convert to a string
        :return: the generated string
        :rtype: str
        """
        return str(item)

    def _compare_regression(self, current: str):
        """
        Compares the current results from the regression test with the ones
        stored on disk. Fails if different. Stores the results if none present yet.

        :param current: the results to compare with
        :type current: str
        """
        reg_file = self._regression_file()

        # any result stored?
        if not os.path.exists(reg_file):
            with open(reg_file, "w") as fp:
                fp.write(current)
            return

        # current result
        current = current.split("\n")

        # load previous result
        with open(reg_file, "r") as fp:
            previous = fp.readlines()
        previous = [line.replace("\n", "") for line in previous]

        # do they match?
        matcher = SequenceMatcher(a=previous, b=current)
        if matcher.ratio() == 1.0:
            return

        # generate detailed diff
        diff = difflib.unified_diff(a=previous, b=current)
        self.fail("Regression test results differ:\n%s" % "\n".join(diff))
