from .pixel_selector import PixelSelector
import random
import numpy as np


class ColumnWisePixelSelector(PixelSelector):
    def __init__(self, reader, n, criteria, c):
        super().__init__(reader, n, criteria)
        self.c = c

    def to_dict(self):
        data = super().to_dict()
        data['c'] = self.c
        return data
        
    def select_pixels(self):
        pixels = []
        for x, y in self._get_candidate_pixels():
            # find some random pixels in the column and average
            if x is None:
                print("!!NONE")
            column_pixels=[]
            all_ys = list(range(self.reader.height))
            random.shuffle(all_ys)
            
            enough = False
            for num in all_ys:
                if self.criteria.check(x, num):
                    column_pixels.append(self.reader.get_spectrum(x, num))
                if len(column_pixels) == self.c:
                    enough=True
                    break
            if not enough:
                break
            pixel_value = np.mean(column_pixels, axis =0)
            pixels.append((x, y, pixel_value))
            if len(pixels) == self.n:
                break
        return pixels
