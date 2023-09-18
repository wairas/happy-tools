import numpy as np
from .pixel_selector import PixelSelector


class AveragedGridSelector(PixelSelector):
    def __init__(self, n, grid_size, criteria=None, include_background=False):
        super().__init__(n, criteria=criteria,include_background=include_background)
        self.grid_size = grid_size

    def to_dict(self):
        data = super().to_dict()
        data['grid_size'] = self.grid_size
        return data

    def get_at(self, happy_data, x, y):
        # Get the pixel data at the specified location (x, y) from the happy_data
        width, height = happy_data.width, happy_data.height
        x0, x1 = max(0, x - self.grid_size), min(width - 1, x + self.grid_size)
        y0, y1 = max(0, y - self.grid_size), min(height - 1, y + self.grid_size)
        
        results = [self.check(happy_data, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
        if all(results):  # all pass
            z_list = [happy_data.get_spectrum(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
            pixel_value = np.mean(z_list, axis=0)
            return pixel_value
        return None
