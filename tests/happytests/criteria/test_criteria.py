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

        self._compare_regression("\n------\n".join(regression_data))
