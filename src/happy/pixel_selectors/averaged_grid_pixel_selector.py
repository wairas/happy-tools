import numpy as np
from happy_hsi2csv.pixel_selectors.pixel_selector import PixelSelector


class AveragedGridSelector(PixelSelector):

    def __init__(self, reader=None, n=None, criteria=None, grid_size=None):
        super().__init__(reader=reader, n=n, criteria=criteria)
        self.grid_size = grid_size

    def to_dict(self):
        d = super().to_dict()
        d['grid_size'] = self.grid_size
        return d

    def from_dict(self, d):
        super().from_dict(d)
        self.grid_size = d['grid_size']

    def select_pixels(self):
        pixels = []
        width = self.reader.width
        height = self.reader.height
        for x, y in self._get_candidate_pixels():
            # Compute the average of the grid around the pixel
            x0, x1 = max(0, x - self.grid_size), min(width - 1, x + self.grid_size)
            y0, y1 = max(0, y - self.grid_size), min(height - 1, y + self.grid_size)
            results = [self.criteria.check(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
            if all(results):  # all pass
                z_list = [self.reader.get_spectrum(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
                pixel_value = np.mean(z_list, axis=0)
                pixels.append((x, y, pixel_value))
                if len(pixels) == self.n:
                    break
        return pixels
