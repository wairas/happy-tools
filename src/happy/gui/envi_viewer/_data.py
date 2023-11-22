import numpy as np
import spectral.io.envi as envi
import traceback

from ._contours import ContoursManager, Contour
from happy.console.hsi_to_rgb.generate import normalize_data
from happy.data.black_ref import AbstractBlackReferenceMethod, AbstractAnnotationBasedBlackReferenceMethod
from happy.data.white_ref import AbstractWhiteReferenceMethod, AbstractAnnotationBasedWhiteReferenceMethod
from happy.data.ref_locator import AbstractReferenceLocator, AbstractFileBasedReferenceLocator, AbstractOPEXAnnotationBasedReferenceLocator
from happy.preprocessors import MultiPreprocessor
from seppl import get_class_name
from opex import BBox


CALC_BLACKREF_APPLIED = "blackref_applied"
CALC_WHITEREF_APPLIED = "whiteref_applied"
CALC_PREPROCESSORS_APPLIED = "preprocessors_applied"
CALC_DIMENSIONS_DIFFER = "dimensions_differ"


class DataManager:
    """
    For managing the loaded data.
    """

    def __init__(self, contours, log_method=None):
        """
        Initializes the manager.

        :param contours: the contours manager
        :type contours: ContoursManager
        :param log_method: the log method to use (only takes a single str arg, the message)
        """
        # _file: the filename
        # _img: the ENVI data structure
        # _data: the numpy data
        self.scan_file = None
        self.scan_img = None
        self.scan_data = None
        self.blackref_locator = None
        self.blackref_method = None
        self.blackref_file = None
        self.blackref_img = None
        self.blackref_data = None
        self.blackref_annotation = None
        self.whiteref_locator = None
        self.whiteref_method = None
        self.whiteref_file = None
        self.whiteref_img = None
        self.whiteref_data = None
        self.whiteref_annotation = None
        self.norm_data = None
        self.display_image = None
        self.wavelengths = None
        self.contours = contours
        self.preprocessors = None
        self.log_method = log_method

    def log(self, msg):
        """
        Logs the message.

        :param msg: the message to log
        :type msg: str
        """
        if self.log_method is not None:
            self.log_method(msg)
        else:
            print(msg)

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
            if len(self.get_wavelengths()) != self.get_num_bands_scan():
                return "Number of defined wavelengths and number of bands in data differ: %d != %d" % (len(self.get_wavelengths()), self.get_num_bands_scan())
        return None

    def get_num_bands_scan(self):
        """
        Returns the number of bands in the scan.

        :return: the number of bands, 0 if no scan present
        :rtype: int
        """
        if not self.has_scan():
            return 0

        return self.scan_data.shape[2]

    def get_num_bands_norm(self):
        """
        Returns the number of bands in the normalized/preprocessed data.

        :return: the number of bands, bands of scan if not present
        :rtype: int
        """
        if self.norm_data is None:
            return self.get_num_bands_scan()

        return self.norm_data.shape[2]

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
                for i in range(len(metadata["wavelength"])):
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
        self.reset_norm_data()

    def set_whiteref_method(self, method):
        """
        Sets the method for applying the white reference.
        
        :param method: the method
        :type method: AbstractWhiteReferenceMethod 
        """
        self.whiteref_method = method
        self.reset_norm_data()

    def set_whiteref_locator(self, locator):
        """
        Sets the locator for the white reference.
        
        :param locator: the locator to use
        :type locator: AbstractReferenceLocator 
        """
        self.whiteref_locator = locator
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
        self.whiteref_file = path
        self.whiteref_img = img
        self.whiteref_data = data
        self.whiteref_annotation = None
        self.reset_norm_data()
        return None

    def set_whiteref_data(self, data):
        """
        Sets the white reference data (when not loading from a file).

        :param data: the reference data
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        self.whiteref_file = None
        self.whiteref_img = None
        self.whiteref_data = data
        self.whiteref_annotation = None
        self.reset_norm_data()
        return None

    def set_whiteref_annotation(self, ann):
        """
        Sets the white reference annotation tuple.

        :param ann: the annotation rectangle to use (top,left,bottom,right)
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        self.whiteref_file = None
        self.whiteref_img = None
        self.whiteref_data = None
        self.whiteref_annotation = ann
        self.reset_norm_data()
        return None

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

    def set_blackref_locator(self, locator):
        """
        Sets the locator for the black reference.

        :param locator: the locator to use
        :type locator: AbstractReferenceLocator 
        """
        self.blackref_locator = locator
        self.reset_norm_data()

    def set_blackref_method(self, method):
        """
        Sets the method for applying the black reference.

        :param method: the method
        :type method: AbstractBlackReferenceMethod
        """
        self.blackref_method = method
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
        self.blackref_file = path
        self.blackref_img = img
        self.blackref_data = data
        self.blackref_annotation = None
        self.reset_norm_data()
        return None

    def set_blackref_data(self, data):
        """
        Sets the black reference data (when not loading from a file).

        :param data: the reference data
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        self.blackref_file = None
        self.blackref_img = None
        self.blackref_data = data
        self.blackref_annotation = None
        self.reset_norm_data()
        return None

    def set_blackref_annotation(self, ann):
        """
        Sets the black reference annotation tuple.

        :param ann: the annotation rectangle to use (top,left,bottom,right)
        :return: None if successfully added, otherwise error message
        :rtype: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        self.blackref_file = None
        self.blackref_img = None
        self.blackref_data = None
        self.blackref_annotation = ann
        self.reset_norm_data()
        return None

    def set_preprocessors(self, preprocessors):
        """
        Sets the pipeline of preprocessors to use.

        :param preprocessors: the list of preprocessors to use or None for no preprocessing
        :type preprocessors: list
        """
        if isinstance(preprocessors, list) and (len(preprocessors) == 0):
            preprocessors = None
        else:
            preprocessors = MultiPreprocessor(**{'preprocessor_list': preprocessors})
        self.preprocessors = preprocessors
        self.reset_norm_data()

    def reset_norm_data(self):
        """
        Resets the normalized data, forcing a recalculation.
        """
        self.norm_data = None

    def init_blackref_data(self):
        """
        Initializes the black reference data, if necessary.
        """
        if self.blackref_data is not None:
            return
        if self.blackref_locator is None:
            return
        if isinstance(self.blackref_locator, AbstractFileBasedReferenceLocator):
            if self.scan_file is not None:
                self.blackref_locator.base_file = self.scan_file
                ref = self.blackref_locator.locate()
                if ref is not None:
                    self.log("Using black reference file: %s" % ref)
                    self.set_blackref(ref)
        elif isinstance(self.blackref_locator, AbstractOPEXAnnotationBasedReferenceLocator):
            dims = self.scan_data.shape
            annotations = self.contours.to_opex(dims[0], dims[1])
            if annotations is not None:
                self.blackref_locator.annotations = annotations
                ref = self.blackref_locator.locate()
                if ref is not None:
                    self.log("Using black reference annotation: %s" % str(ref.bbox))
                    self.set_blackref_annotation((ref.bbox.top, ref.bbox.left, ref.bbox.bottom, ref.bbox.right))
        else:
            ref = self.blackref_locator.locate()
            if ref is not None:
                if isinstance(ref, str):
                    self.log("Using black reference file: %s" % ref)
                    self.set_blackref(ref)
                else:
                    raise Exception("Unhandled output of black reference locator %s: %s" % (self.blackref_locator.name(), get_class_name(ref)))

    def init_whiteref_data(self):
        """
        Initializes the white reference data, if necessary.
        """
        if self.whiteref_data is not None:
            return
        if self.whiteref_locator is None:
            return
        if isinstance(self.whiteref_locator, AbstractFileBasedReferenceLocator):
            if self.scan_file is not None:
                self.whiteref_locator.base_file = self.scan_file
                ref = self.whiteref_locator.locate()
                if ref is not None:
                    self.log("Using white reference file: %s" % ref)
                    self.set_whiteref(ref)
        elif isinstance(self.whiteref_locator, AbstractOPEXAnnotationBasedReferenceLocator):
            dims = self.scan_data.shape
            annotations = self.contours.to_opex(dims[0], dims[1])
            if annotations is not None:
                self.whiteref_locator.annotations = annotations
                ref = self.whiteref_locator.locate()
                if ref is not None:
                    self.log("Using white reference annotation: %s" % str(ref.bbox))
                    self.set_whiteref_annotation((ref.bbox.top, ref.bbox.left, ref.bbox.bottom, ref.bbox.right))
        else:
            ref = self.whiteref_locator.locate()
            if ref is not None:
                if isinstance(ref, str):
                    self.log("Using white reference file: %s" % ref)
                    self.set_whiteref(ref)
                else:
                    raise Exception("Unhandled output of white reference locator %s: %s" % (self.whiteref_locator.name(), get_class_name(ref)))

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

    def calc_norm_data(self):
        """
        Calculates the normalized data.

        :return: which steps succeeded
        :rtype: dict
        """
        result = dict()
        if self.norm_data is not None:
            return result
        if self.scan_data is not None:
            self.log("Calculating...")
            try:
                # some initialization
                self.init_blackref_data()
                self.init_whiteref_data()
                self.norm_data = self.scan_data
                # apply black reference
                if self.blackref_method is not None:
                    if (self.blackref_annotation is not None) and isinstance(self.blackref_method, AbstractAnnotationBasedBlackReferenceMethod):
                        self.log("Applying black reference method: %s" % self.blackref_method.name())
                        result[CALC_BLACKREF_APPLIED] = False
                        self.blackref_method.reference = self.scan_data
                        self.blackref_method.annotation = self.blackref_annotation
                        self.norm_data = self.blackref_method.apply(self.norm_data)
                        result[CALC_BLACKREF_APPLIED] = True
                    elif self.blackref_data is not None:
                        self.log("Applying black reference method: %s" % self.blackref_method.name())
                        result[CALC_BLACKREF_APPLIED] = False
                        self.blackref_method.reference = self.blackref_data
                        self.norm_data = self.blackref_method.apply(self.norm_data)
                        result[CALC_BLACKREF_APPLIED] = True
                # apply white reference
                if self.whiteref_method is not None:
                    if (self.whiteref_annotation is not None) and isinstance(self.whiteref_method, AbstractAnnotationBasedWhiteReferenceMethod):
                        self.log("Applying white reference method: %s" % self.whiteref_method.name())
                        result[CALC_WHITEREF_APPLIED] = False
                        self.whiteref_method.reference = self.scan_data
                        self.whiteref_method.annotation = self.whiteref_annotation
                        self.norm_data = self.whiteref_method.apply(self.norm_data)
                        result[CALC_WHITEREF_APPLIED] = True
                    elif self.whiteref_data is not None:
                        self.log("Applying white reference method: %s" % self.whiteref_method.name())
                        result[CALC_WHITEREF_APPLIED] = False
                        self.whiteref_method.reference = self.whiteref_data
                        self.norm_data = self.whiteref_method.apply(self.norm_data)
                        result[CALC_WHITEREF_APPLIED] = True
                # apply preprocessing
                if self.preprocessors is not None:
                    self.log("Applying preprocessing: %s" % str(self.preprocessors))
                    result[CALC_PREPROCESSORS_APPLIED] = False
                    self.norm_data, _ = self.preprocessors.apply(self.norm_data)
                    result[CALC_PREPROCESSORS_APPLIED] = True
                self.log("...done!")
            except:
                self.log("...failed with exception:")
                self.log(traceback.format_exc())

            if self.norm_data is not None:
                result[CALC_DIMENSIONS_DIFFER] = (self.scan_data.shape != self.norm_data.shape)

        return result

    def update_image(self, r, g, b):
        """
        Updates the image.

        :param r: the red channel to use
        :type r: int
        :param g: the green channel to use
        :type g: int
        :param b: the blue channel to use
        :type b: int
        :return: which steps succeeded
        :rtype: dict
        """
        if self.scan_data is None:
            return dict()

        success = self.calc_norm_data()

        if self.norm_data is not None:
            num_bands = self.get_num_bands_norm()
            r = min(r, num_bands - 1)
            g = min(g, num_bands - 1)
            b = min(b, num_bands - 1)
            red_band = self.norm_data[:, :, r]
            green_band = self.norm_data[:, :, g]
            blue_band = self.norm_data[:, :, b]

            norm_red = normalize_data(red_band)
            norm_green = normalize_data(green_band)
            norm_blue = normalize_data(blue_band)

            rgb_image = np.dstack((norm_red, norm_green, norm_blue))
            self.display_image = (rgb_image * 255).astype(np.uint8)

        return success

    def get_scan_subimage(self, contour=None, bbox=None):
        """
        Returns the sub-image of the scan that encompasses the bbox of the contour.

        :param contour: the contour to use for extracting the subset of the scan
        :type contour: Contour
        :param bbox: the OPEX BBox to use
        :type bbox: BBox
        :return: the sub-image of the scan, None if no scan
        """
        if not self.has_scan():
            return None

        h, w, _ = self.scan_data.shape
        
        if contour is not None:
            bbox = contour.to_absolute(w, h).bbox()
            result = self.scan_img[bbox.top:bbox.bottom, bbox.left:bbox.right, :]
            return result
        
        if bbox is not None:
            result = self.scan_img[bbox.top:bbox.bottom, bbox.left:bbox.right, :]
            return result

        return None
