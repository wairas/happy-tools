import numpy as np
import spectral.io.envi as envi

from happy.console.hsi_to_rgb.generate import normalize_data
from happy.gui.envi_viewer import LABEL_WHITEREF


class DataManager:
    """
    For managing the loaded data.
    """

    def __init__(self, contours):
        """
        Initializes the manager.

        :param contours: the contours manager
        :type contours: ContoursManager
        """
        # _file: the filename
        # _img: the ENVI data structure
        # _data: the numpy data
        self.scan_file = None
        self.scan_img = None
        self.scan_data = None
        self.blackref_file = None
        self.blackref_img = None
        self.blackref_data = None
        self.whiteref_file = None
        self.whiteref_img = None
        self.whiteref_data = None
        self.norm_data = None
        self.display_image = None
        self.wavelengths = None
        self.contours = contours
        self.use_whiteref_annotation = False
        self.whiteref_annotation = None

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
        self.scan_img = None
        self.scan_data = None
        self.wavelengths = None
        self.reset_norm_data()

    def set_scan(self, path):
        """
        Sets the scan.

        :param path: the filename
        :type path: str
        :return: None if successfully loaded, otherwise an error/warning message
        :rtype: str
        """
        img = envi.open(path)
        self.scan_file = path
        self.scan_img = img
        self.scan_data = img.load()
        self.reset_norm_data()
        if len(self.get_wavelengths()) > 0:
            if len(self.get_wavelengths()) != self.get_num_bands():
                return "Number of defined wavelengths and number of bands in data differ: %d != %d" % (len(self.get_wavelengths()), self.get_num_bands())
        return None

    def get_num_bands(self):
        """
        Returns the number of bands in the scan.

        :return: the number of bands, 0 if no scan present
        :rtype: int
        """
        if not self.has_scan():
            return 0

        return self.scan_data.shape[2]

    def get_wavelengths(self):
        """
        Returns the indexed wave lengths.

        :return: the dictionary of the wave band / wave length association, empty if no scan present
        :rtype: dict
        """
        if not self.has_scan():
            return dict()

        if self.wavelengths is None:
            self.wavelengths = dict()
            metadata = self.scan_img.metadata
            if "wavelength" in metadata:
                for i in range(self.get_num_bands()):
                    self.wavelengths[i] = metadata["wavelength"][i]

        return self.wavelengths

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
        self.whiteref_img = None
        self.whiteref_data = None
        self.whiteref_annotation = None
        self.reset_norm_data()

    def set_whiteref(self, path):
        """
        Sets the white reference.

        :param path: the filename
        :type path: str
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        img = envi.open(path)
        data = img.load()
        if data.shape != self.scan_data.shape:
            return "White reference data should have the same shape as the scan data!\n" \
                   + "scan:" + str(self.scan_data.shape) + " != whiteref:" + str(data.shape)

        self.whiteref_file = path
        self.whiteref_img = img
        self.whiteref_data = data
        self.whiteref_annotation = None
        self.reset_norm_data()
        return None

    def get_whiteref_annotation(self):
        """
        Returns the whiteref value to use for normalizing, calculates it if necessary.

        :return: the whiteref annotation value
        :rtype: float
        """
        if self.whiteref_annotation is None:
            contours = self.contours.get_contours(LABEL_WHITEREF)
            if len(contours) == 1:
                whiteref_img = self.get_scan_subimage(contours[0])
                self.whiteref_annotation = np.average(whiteref_img)
            elif len(contours) > 1:
                print("More than one '%s' annotation found!" % LABEL_WHITEREF)
            else:
                self.whiteref_annotation = 1.0

        return self.whiteref_annotation

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
        self.blackref_img = None
        self.blackref_data = None
        self.reset_norm_data()

    def set_blackref(self, path):
        """
        Sets the black reference.

        :param path: the filename
        :type path: str
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        img = envi.open(path)
        data = img.load()
        if data.shape != self.scan_data.shape:
            return "Black reference data should have the same shape as the scan data!\n" \
                   + "scan:" + str(self.scan_data.shape) + " != blackref:" + str(data.shape)

        self.blackref_file = path
        self.blackref_img = img
        self.blackref_data = data
        self.reset_norm_data()
        return None

    def reset_norm_data(self):
        """
        Resets the normalized data, forcing a recalculation.
        """
        self.norm_data = None
        self.whiteref_annotation = None

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
                if self.blackref_data.shape == self.norm_data.shape:
                    self.norm_data = self.norm_data - self.blackref_data
                else:
                    print("Scan and blackref dimensions differ: %s != %s" % (str(self.scan_data.shape), str(self.blackref_data.shape)))
            # divide by white reference
            if self.use_whiteref_annotation:
                if self.get_whiteref_annotation() != 1.0:
                    self.norm_data = self.norm_data / self.get_whiteref_annotation()
            else:
                if self.whiteref_data is not None:
                    if self.whiteref_data.shape == self.norm_data.shape:
                        self.norm_data = self.norm_data / self.whiteref_data
                    else:
                        print("Scan and whiteref dimensions differ: %s != %s" % (str(self.scan_data.shape), str(self.whiteref_data.shape)))

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

    def get_scan_subimage(self, contour):
        """
        Returns the subimage of the scan that encompasses the bbox of the contour.

        :param contour: the contour to use for extracting the subset of the scan
        :type contour: Contour
        :return: the sub-image of the scan, None if no scane
        """
        if not self.has_scan():
            return None

        h, w, _ = self.scan_data.shape
        bbox = contour.to_absolute(w, h).bbox()
        result = self.scan_img[bbox.top:bbox.bottom, bbox.left:bbox.right, :]
        return result
