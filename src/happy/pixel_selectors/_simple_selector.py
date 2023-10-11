from ._base_pixel_selector import BasePixelSelector


class SimpleSelector(BasePixelSelector):

    def __init__(self, n=0,  criteria=None, include_background=False):
        super().__init__(n, criteria=criteria,include_background=include_background)
        
    def get_at(self, happy_data, x, y):
        return happy_data.get_spectrum(x, y)
