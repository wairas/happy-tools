import random


class PixelSelector:
    def __init__(self, n, criteria=None, include_background=False):
        self.n = n
        self.criteria = criteria
        self.include_background = include_background
        #self.happy_data = None

    #def set_happy_data(self, happy_data):
    #    self.happy_data = happy_data
        
    def get_n(self):
        return(self.n)
        
    def set_criteria(self, criteria):
        self.criteria = criteria
        
    def check(self, happy_data, x,y,):
        if self.criteria is None:
            return(True)
        else:
            return(self.criteria.check(happy_data, x, y))
          
    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'n': self.n,
            #'data': self.happy_data.to_dict(),
            'criteria' : self.criteria.to_dict()
        }

        
    def get_at(self, happy_data, x, y):
        raise NotImplementedError("Subclasses must implement the get_at method")
    
    def _get_candidate_pixels(self, happy_data):
        # This is a generator function that yields candidate pixels
        # until `n` pixels that match the criteria are found.
        i = 0
        pos = 0
        #z_data = self.reader.get_spectrum(0,0) #get a z_data example, for dimensions
        #print(z_data.shape)
        all_pixel_coords = happy_data.get_all_xy_pairs(self.include_background) 
        #print(all_pixel_coords)
        random.shuffle(all_pixel_coords)
        #print(i)
        #print(len(all_pixel_coords))
        while i < len(all_pixel_coords) and pos < len(all_pixel_coords):
            #print(pos)
            x,y = all_pixel_coords[pos]
            pos = pos + 1
            #x = random.randint(0, z_data.shape[0] - 1)
            #y = random.randint(0, z_data.shape[1] - 1)
            if self.check(happy_data, x,y):
                    i += 1
                    yield x, y

    def get_all_pixels(self, happy_data):
        return self.select_pixels(happy_data, n=-1)
        
    def select_pixels(self, happy_data, n=None):
        pixels = []
        if n is None:
            n = self.n

        for x, y in self._get_candidate_pixels(happy_data):
            pixel_value = self.get_at(happy_data, x, y)
            if pixel_value is not None:
                pixels.append((x, y, pixel_value))
            if len(pixels) == n:
                break
        return pixels
