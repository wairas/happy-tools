import numpy as np
import spectral.io.envi as envi
import traceback

from typing import List, Dict, Optional

from PIL import Image
from happy.data import HappyData
from happy.data.annotations import ContoursManager, Contour
from happy.data.black_ref import AbstractBlackReferenceMethod, AbstractAnnotationBasedBlackReferenceMethod
from happy.data.white_ref import AbstractWhiteReferenceMethod, AbstractAnnotationBasedWhiteReferenceMethod
from happy.data.ref_locator import AbstractReferenceLocator, AbstractFileBasedReferenceLocator, AbstractOPEXAnnotationBasedReferenceLocator
from happy.data.normalization import AbstractNormalization, SimpleNormalization, AbstractOPEXAnnotationBasedNormalization
from happy.preprocessors import MultiPreprocessor
from seppl import get_class_name
from opex import BBox, ObjectPredictions


CALC_BLACKDATA_INITIALIZED = "blackdata_initialized"
CALC_WHITEDATA_INITIALIZED = "whitedata_initialized"
CALC_BLACKREF_APPLIED = "blackref_applied"
CALC_WHITEREF_APPLIED = "whiteref_applied"
CALC_PREPROCESSORS_APPLIED = "preprocessors_applied"
CALC_DIMENSIONS_DIFFER = "dimensions_differ"


class DataManager:
    """
    For managing the loaded data.
    """

    def __init__(self, contours=None, log_method=None):
        """
        Initializes the manager.

        :param contours: the contours manager, creates one automatically if None
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
        self.contours = contours if (contours is not None) else ContoursManager()
        self.preprocessors = None
        self.normalization = SimpleNormalization()
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

    def get_wavelengths(self) -> Dict:
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

    def get_wavelengths_list(self) -> List[float]:
        """
        Returns the wavelengths as list rather than a dictionary.

        :return: the wavelengths
        :rtype: list
        """
        result = []
        wl = self.get_wavelengths()
        for k in wl:
            result.append(float(wl[k]))
        return result

    def set_wavelengths_list(self, wl: Optional[List]):
        """
        Uses the wavelengths from the list.

        :param wl: the list of wavelengths to use; auto-generates dummy ones if None
        :type wl: list
        """
        wl_dict = dict()
        if wl is not None:
            for i in range(len(wl)):
                wl_dict[i] = str(wl[i])
        else:
            for i in range(self.get_num_bands_norm()):
                wl_dict[i] = str(i)
        self.wavelengths = wl_dict

    def has_annotations(self):
        """
        Checks whether any contours are present.

        :return: True if contours are present
        :rtype: bool
        """
        return self.contours.has_contours()

    def clear_annotations(self):
        """
        Removes all currently set contours.
        """
        self.contours.clear()

    def set_annotations(self, path):
        """
        Loads the annotations in OPEX JSON format.

        :param path: the OPEX JSON file to load
        :type path: str
        """
        if not self.has_scan():
            return "Please load a scan first!"

        ann = ObjectPredictions.load_json_from_file(path)
        self.contours.from_opex(ann, self.scan_data.shape[1], self.scan_data.shape[0])
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

    def can_init_blackref_data(self):
        """
        Whether blackref data can be initialized

        :return: True if it can be initialized
        :rtype: bool
        """
        if self.blackref_data is not None:
            return False
        if self.blackref_locator is None:
            return False
        return True

    def init_blackref_data(self):
        """
        Initializes the black reference data, if necessary.
        """
        if not self.can_init_blackref_data():
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
            annotations = self.contours.to_opex(dims[1], dims[0])
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

    def can_init_whiteref_data(self):
        """
        Whether whiteref data can be initialized

        :return: True if it can be initialized
        :rtype: bool
        """
        if self.whiteref_data is not None:
            return False
        if self.whiteref_locator is None:
            return False
        return True

    def init_whiteref_data(self):
        """
        Initializes the white reference data, if necessary.
        """
        if not self.can_init_whiteref_data():
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
            annotations = self.contours.to_opex(dims[1], dims[0])
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
            self.log("Calculation: start")
            success = True

            # init blackref
            try:
                if success and self.can_init_blackref_data():
                    result[CALC_BLACKDATA_INITIALIZED] = False
                    self.log("Initializing black reference data: %s" % self.blackref_locator.name())
                    self.init_blackref_data()
                    result[CALC_BLACKDATA_INITIALIZED] = True
            except:
                success = False
                self.log("Calculation: failed with exception:")
                self.log(traceback.format_exc())

            # init whiteref
            try:
                if success and self.can_init_whiteref_data():
                    result[CALC_WHITEDATA_INITIALIZED] = False
                    self.log("Initializing white reference data: %s" % self.whiteref_locator.name())
                    self.init_whiteref_data()
                    result[CALC_WHITEDATA_INITIALIZED] = True
            except:
                success = False
                self.log("Calculation: failed with exception:")
                self.log(traceback.format_exc())

            if success:
                self.norm_data = self.scan_data

            # apply black reference
            try:
                if success and self.blackref_method is not None:
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
            except:
                success = False
                self.log("Calculation: failed with exception:")
                self.log(traceback.format_exc())

            # apply white reference
            try:
                if success and self.whiteref_method is not None:
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
            except:
                success = False
                self.log("Calculation: failed with exception:")
                self.log(traceback.format_exc())

            # apply preprocessing
            try:
                if success and self.preprocessors is not None:
                    self.log("Applying preprocessing: %s" % str(self.preprocessors))
                    result[CALC_PREPROCESSORS_APPLIED] = False
                    wl = self.get_wavelengths_list()
                    happy_data = HappyData("envi-viewer", "1", self.norm_data, {}, {}, wavenumbers=wl)
                    self.preprocessors.fit(happy_data)
                    new_happy_data = self.preprocessors.apply(happy_data)
                    if len(new_happy_data) == 1:
                        self.norm_data = new_happy_data[0].data
                        if new_happy_data[0].wavenumbers is not None:
                            if wl != new_happy_data[0].wavenumbers:
                                self.set_wavelengths_list(new_happy_data[0].wavenumbers)
                        else:
                            self.set_wavelengths_list(None)
                    else:
                        self.log("Preprocessing: preprocessors did not generate just a single output, but: %d" % len(new_happy_data))
                    result[CALC_PREPROCESSORS_APPLIED] = True
            except:
                success = False
                self.log("Calculation: failed with exception:")
                self.log(traceback.format_exc())

            if success:
                self.log("Calculation: done!")

            if self.norm_data is not None:
                result[CALC_DIMENSIONS_DIFFER] = (self.scan_data.shape != self.norm_data.shape)

        return result

    def _calc_norm_data_indicator(self, v):
        """
        Turns the boolean value into an indicator string.

        :param v: the boolean value
        :type v: bool
        :return: the generated string
        """
        if v:
            return "✔"  # u2714
        else:
            return "❌"  # u274c

    def calc_norm_data_indicator(self, d):
        """
        Turns the dictionary returned by the calc_norm_data method into an indicator string.

        :param d: the dictionary to turn into an indicator string
        :type d: dict
        :return: the generated string
        :rtype: str
        """
        result = ""
        if (CALC_BLACKDATA_INITIALIZED in d) or (CALC_WHITEDATA_INITIALIZED in d):
            success = ((CALC_BLACKDATA_INITIALIZED in d) and (d[CALC_BLACKDATA_INITIALIZED])) \
                      or ((CALC_WHITEDATA_INITIALIZED in d) and (d[CALC_WHITEDATA_INITIALIZED]))
            result += "I:" + self._calc_norm_data_indicator(success) + " "
        if CALC_BLACKREF_APPLIED in d:
            result += "B:" + self._calc_norm_data_indicator(d[CALC_BLACKREF_APPLIED]) + " "
        if CALC_WHITEREF_APPLIED in d:
            result += "W:" + self._calc_norm_data_indicator(d[CALC_WHITEREF_APPLIED]) + " "
        if CALC_PREPROCESSORS_APPLIED in d:
            result += "P:" + self._calc_norm_data_indicator(d[CALC_PREPROCESSORS_APPLIED]) + " "
        if CALC_DIMENSIONS_DIFFER in d:
            result += "D:" + self._calc_norm_data_indicator(not d[CALC_DIMENSIONS_DIFFER]) + " "
        result = result.strip()
        return result

    def set_normalization(self, normalization):
        """
        Sets the normalization scheme to use.
        Caller needs to call update_image(r, g, b) to re-calculate the fake RGB image.

        :param normalization: the normalization scheme, None turns off normalization
        :type normalization: AbstractNormalization
        """
        self.normalization = normalization

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

            norm_red = red_band
            norm_green = green_band
            norm_blue = blue_band
            if self.normalization is not None:
                if isinstance(self.normalization, AbstractOPEXAnnotationBasedNormalization):
                    self.normalization.annotations = self.contours.to_opex(self.norm_data.shape[1], self.norm_data.shape[0])
                try:
                    norm_red = self.normalization.normalize(red_band)
                    norm_green = self.normalization.normalize(green_band)
                    norm_blue = self.normalization.normalize(blue_band)
                except:
                    self.log("Failed to normalize image using r=%d, g=%d, b=%d:\n%s" % (r, g, b, traceback.format_exc()))

            rgb_image = np.dstack((norm_red, norm_green, norm_blue))
            self.display_image = (rgb_image * 255).astype(np.uint8)

        return success

    def output_image(self, r, g, b, output, width=0, height=0):
        """
        Updates the image and saves it to the specified file.

        :param r: the red channel to use
        :type r: int
        :param g: the green channel to use
        :type g: int
        :param b: the blue channel to use
        :type b: int
        :param output: the file to save the image to
        :type output: str
        :param width: the custom width to use, ignored if <=0
        :type width: int
        :param height: the custom height to use, ignored if <=0
        :type height: int
        """
        self.update_image(r, g, b)
        image = Image.fromarray(self.display_image)
        act_width, act_height = image.size
        if width > 0:
            act_width = width
        if height > 0:
            act_height = height
        image = image.resize((act_width, act_height), Image.LANCZOS)
        image.save(output)

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
