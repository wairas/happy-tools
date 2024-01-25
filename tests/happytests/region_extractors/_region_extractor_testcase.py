import abc
import copy
from typing import List

from happy.data import HappyData
from happy.region_extractors import RegionExtractor
from happytests.tests import HappyDataTestCase


class RegionExtractorTestCase(HappyDataTestCase, abc.ABC):

    def _regression_setup(self) -> List[RegionExtractor]:
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
        region_extractors = self._regression_setup()
        if len(region_extractors) == 0:
            return
        data = self._regression_data()
        processed_data = []
        for region_extractor in region_extractors:
            for item in data:
                regions = region_extractor.extract_regions(item)
                processed_data.extend(regions)
        regression_data = []
        for item in processed_data:
            regression_data.append(self._regression_item_to_str(item))
        self._compare_regression("\n------\n".join(regression_data))
