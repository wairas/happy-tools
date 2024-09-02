from ._happydata_writer import PH_BASEDIR, PH_SAMPLEID, PH_REPEAT
from ._image_writer import ImageWriter


class PNGWriter(ImageWriter):

    def name(self) -> str:
        return "png-writer"

    def description(self) -> str:
        return "Generates PNG images from the data.\nDEPRECATED: Use 'image-writer' instead."

    def _get_default_output(self):
        return PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".png"
