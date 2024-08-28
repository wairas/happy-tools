from ._happydata_writer import PH_BASEDIR, PH_SAMPLEID, PH_REPEAT
from ._image_writer import ImageWriter


class JPGWriter(ImageWriter):

    def __init__(self, base_dir=None):
        super().__init__(base_dir=base_dir)

    def name(self) -> str:
        return "jpg-writer"

    def description(self) -> str:
        return "Generates JPEG images from the data."

    def _get_default_output(self):
        return PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".jpg"
