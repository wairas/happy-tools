import numpy as np
from .pixel_selector import PixelSelector


class AveragedGridSelector(PixelSelector):
    def __init__(self, reader, n, criteria, grid_size):
        super().__init__(reader, n, criteria)
        self.grid_size = grid_size

    def to_dict(self):
        data = super().to_dict()
        data['grid_size'] = self.grid_size
        return data

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
