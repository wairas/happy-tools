import os
import unittest

from happy.base.core import ConfigurableObject
from happy.criteria import Criteria, CriteriaGroup, OP_NOT_MISSING, OP_EQUALS
from happytests.tests import HappyRegressionTestCase


class CriteriaTestCase(HappyRegressionTestCase):

    def test_regression(self):
        """
        Performs the regression test.
        """
        self._init_regression_dir()
        regression_data = []

        c1 = Criteria(operation=OP_NOT_MISSING, key="type", value=[2, 3])
        regression_data.append(str(c1))
        regression_data.append(str(c1.to_json()))
        cn1 = ConfigurableObject.from_json(c1.to_json())
        regression_data.append(str(cn1))

        c2 = Criteria(operation=OP_EQUALS, key="type", value=1)
        regression_data.append(str(c2))
        regression_data.append(str(c2.to_json()))
        cn2 = ConfigurableObject.from_json(c2.to_json())
        regression_data.append(str(cn2))

        cg = CriteriaGroup(criteria_list=[c1, c2])
        regression_data.append(str(cg))
        regression_data.append(str(cg.to_json()))
        cng = ConfigurableObject.from_json(cg.to_json())
        regression_data.append(str(cng))

        c = ConfigurableObject.from_json(os.path.join(self._data_dir(), "criteria.json"))
        self.assertEqual(Criteria, type(c), msg="Incorrect type!")
        regression_data.append(str(c))
        cg = ConfigurableObject.from_json(os.path.join(self._data_dir(), "criteriagroup.json"))
        self.assertEqual(CriteriaGroup, type(cg), msg="Incorrect type!")
        regression_data.append(str(cg))

        self._compare_regression("\n------\n".join(regression_data))

    def test_load_from_file_like_object(self):
        """
        Tests loading from json files.
        """
        with open(os.path.join(self._data_dir(), "criteria.json"), "r") as fp:
            c = ConfigurableObject.from_json(fp)
            self.assertEqual(Criteria, type(c), msg="Incorrect type!")
        with open(os.path.join(self._data_dir(), "criteriagroup.json"), "r") as fp:
            cg = ConfigurableObject.from_json(fp)
            self.assertEqual(CriteriaGroup, type(cg), msg="Incorrect type!")


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    return unittest.TestLoader().loadTestsFromTestCase(CriteriaTestCase)


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
