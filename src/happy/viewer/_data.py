import numpy as np

from happy.hsi_to_rgb.generate import normalize_data


class DataManager:
    """
    For managing the loaded data.
    """

    def __init__(self):
        """
        Initializes the manager.
        """
        self.scan_file = None
        self.scan_data = None
        self.blackref_file = None
        self.blackref_data = None
        self.whiteref_file = None
        self.whiteref_data = None
        self.norm_data = None
        self.display_image = None

    def has_scan(self):
        """
        Checks whether scan data is present.

        :return: True if present
        :rtype: bool
        """
        return self.scan_data is not None

    def clear_scan(self):
        """
        Removes the scan data.
        """
        self.scan_file = None
        self.scan_data = None
        self.reset_norm_data()

    def set_scan(self, fname, data):
        """
        Sets the scan.

        :param fname: the filename
        :type fname: str
        :param data: the scan data
        """
        self.scan_file = fname
        self.scan_data = data
        self.reset_norm_data()

    def has_whiteref(self):
        """
        Checks whether white reference data is present.

        :return: True if present
        :rtype: bool
        """
        return self.whiteref_data is not None

    def clear_whiteref(self):
        """
        Removes the white reference data.
        """
        self.whiteref_file = None
        self.whiteref_data = None
        self.reset_norm_data()

    def set_whiteref(self, fname, data):
        """
        Sets the white reference.

        :param fname: the filename
        :type fname: str
        :param data: the white reference data
        """
        self.whiteref_file = fname
        self.whiteref_data = data
        self.reset_norm_data()

    def has_blackref(self):
        """
        Checks whether black reference data is present.

        :return: True if present
        :rtype: bool
        """
        return self.blackref_data is not None

    def clear_blackref(self):
        """
        Removes the black reference data.
        """
        self.blackref_file = None
        self.blackref_data = None
        self.reset_norm_data()

    def set_blackref(self, fname, data):
        """
        Sets the black reference.

        :param fname: the filename
        :type fname: str
        :param data: the black reference data
        """
        self.blackref_file = fname
        self.blackref_data = data
        self.reset_norm_data()

    def reset_norm_data(self):
        """
        Resets the normalized data, forcing a recalculation.
        """
        self.norm_data = None

    def calc_norm_data(self, log):
        """
        Calculates the normalized data.

        :param log: the method for logging messages in the UI
        """
        if self.norm_data is not None:
            return
        if self.scan_data is not None:
            log("Calculating...")
            self.norm_data = self.scan_data
            # subtract black reference
            if self.blackref_data is not None:
                self.norm_data = self.norm_data - self.blackref_data
            # divide by white reference
            if self.whiteref_data is not None:
                self.norm_data = self.norm_data / self.whiteref_data

    def dims(self):
        """
        Returns the dimensions of the loaded data.

        :return: the tuple (w,h) of the data, None if no data
        :rtype: tuple
        """
        if self.norm_data is None:
            return None
        else:
            return self.norm_data.shape[1], self.norm_data.shape[0]

    def update_image(self, r, g, b, log):
        """
        Updates the image.

        :param r: the red channel to use
        :type r: int
        :param g: the green channel to use
        :type g: int
        :param b: the blue channel to use
        :type b: int
        :param log: the method for logging messages in the UI
        """
        if self.scan_data is None:
            return

        self.calc_norm_data(log)

        red_band = self.norm_data[:, :, r]
        green_band = self.norm_data[:, :, g]
        blue_band = self.norm_data[:, :, b]

        norm_red = normalize_data(red_band)
        norm_green = normalize_data(green_band)
        norm_blue = normalize_data(blue_band)

        rgb_image = np.dstack((norm_red, norm_green, norm_blue))
        self.display_image = (rgb_image * 255).astype(np.uint8)