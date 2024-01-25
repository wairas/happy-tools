import abc
import copy
from typing import List

from happy.data import HappyData
from happy.preprocessors import Preprocessor
from happytests.tests import HappyDataTestCase


class PreprocessorTestCase(HappyDataTestCase, abc.ABC):

    def _regression_setup(self) -> List[Preprocessor]:
        """
        Returns the setups to use in the regression tests.

        :return: the setups
        :rtype: list
        """
        return []

    def _regression_data(self) -> List[HappyData]:
        """
        Returns the data to use for the regression test.

        :return: the happy data
        :rtype: list
        """
        return self.data_92AV3C

    def _regression_item_to_str(self, item) -> str:
        """
        Turns the regression item into a string.

        :param item: the regression item to convert to a string
        :return: the generated string
        :rtype: str
        """
        return repr(item.data.shape) + "\n\n" + repr(item.data)

    def test_regression(self):
        """
        Performs the regression test.
        """
        self._init_regression_dir()
        preprocessors = self._regression_setup()
        if len(preprocessors) == 0:
            return
        data = self._regression_data()
        processed_data = []
        for preprocessor in preprocessors:
            for item in data:
                preprocessor.fit(item.data)
                filtered, metadata = preprocessor.apply(item.data)
                new_data = HappyData(item.sample_id, item.region_id, filtered, copy.deepcopy(item.global_dict), metadata)
                processed_data.append(new_data)
        regression_data = []
        for item in processed_data:
            regression_data.append(self._regression_item_to_str(item))
        self._compare_regression("\n------\n".join(regression_data))
