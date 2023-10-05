from ._pixel_selector import PixelSelector


class MultiSelector(PixelSelector):
    def __init__(self, selectors):
        self.selectors = selectors
        self.n = sum(obj.n for obj in selectors)

    def to_dict(self):
        data = super().to_dict()
        data['selectors'] = [selector.to_dict() for selector in self.selectors]
        return data

    def select_pixels(self, happy_data, n=None):
        pixels = []
        for selector in self.selectors:
            #print(selector.to_dict())
            more_pixels = selector.select_pixels(happy_data)
            #print(len(more_pixels))
            pixels.extend(more_pixels)
        return pixels