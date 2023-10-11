import abc

from happy.base.core import ConfigurableObject
from seppl import Plugin


class PixelSelector(ConfigurableObject, Plugin, abc.ABC):

    def get_n(self):
        raise NotImplementedError()

    def get_all_pixels(self, happy_data):
        return self.select_pixels(happy_data, n=-1)

    def select_pixels(self, happy_data, n=None):
        raise NotImplementedError()
