from ._pixel_selector import PixelSelector


class SimpleSelector(PixelSelector):
    def __init__(self, n,  criteria=None, include_background=False):
        super().__init__(n, criteria=criteria,include_background=include_background)
        
    def get_at(self, happy_data, x, y):
        # Implement this method to return the value at the specified (x, y) coordinates
        return happy_data.get_spectrum(x, y)
