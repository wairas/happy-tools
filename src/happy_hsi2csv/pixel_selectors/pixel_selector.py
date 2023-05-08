import random


class PixelSelector:
    def __init__(self, reader, n, criteria):
        self.reader = reader
        self.n = n
        self.criteria = criteria
        
    def get_n(self):
        return self.n
    
    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'n': self.n,
            'reader': self.reader.to_dict(),
            'criteria' : self.criteria.to_dict()
        }

    def _get_candidate_pixels(self):
        # This is a generator function that yields candidate pixels
        # until `n` pixels that match the criteria are found.
        i = 0
        pos = 0
        all_pixel_coords = [(int(x_str), int(y_str)) for x_str, column_dict in self.reader.json_reader.pixel_dict.items()
                for y_str, pixel_dict in column_dict.items()]
        random.shuffle(all_pixel_coords)
        while i < len(all_pixel_coords) and pos < len(all_pixel_coords):
            x,y = all_pixel_coords[pos]
            pos = pos + 1
            if self.criteria.check(x,y):
                i += 1
                yield x, y

    def select_pixels(self):
        pixels = []
        for x, y in self._get_candidate_pixels():
            z_data = self.reader.get_spectrum(x,y)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
            pixels.append((x, y, z_data))
            if len(pixels) == self.n:
                break
        return pixels
