from typing import Optional, Union

from happy.criteria import Criteria, CriteriaGroup
from happy.data import HappyData
from ._base_pixel_selector import BasePixelSelector


class SimpleSelector(BasePixelSelector):

    def __init__(self, n: int = 0, criteria: Optional[Union[Criteria, CriteriaGroup]] = None, include_background: bool = False):
        super().__init__(n, criteria=criteria, include_background=include_background)

    def name(self) -> str:
        return "ps-simple"

    def description(self) -> str:
        return "Returns the spectrum at the requested x/y location."

    def get_at(self, happy_data: HappyData, x: int, y: int) -> Optional[Union[int, float]]:
        return happy_data.get_spectrum(x, y)
