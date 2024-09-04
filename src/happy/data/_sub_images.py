import os
import traceback
from typing import Optional, Tuple

from happy.data import HappyData, DataManager
from happy.writers import HappyDataWriter, HappyDataWriterWithNormalization, ImageWriter
from happy.data.normalization import SimpleNormalization


def export_sub_images(datamanager: DataManager, path: str, label_regexp: Optional[str], raw: bool,
                      writer_cmdline: str = "happy-writer", rgb: Tuple[int, int, int] = None) -> Optional[str]:
    """
    Exports the sub-images defined in the contours as ENVI files.
    Stores them in the specified directory with the specified prefix (and the label as suffix).

    :param datamanager: the data manager to use for exporting the data
    :type datamanager: DataManager
    :param path: the directory to store the sub-images in
    :type path: str
    :param label_regexp: the label expression to apply, ignored if None or empty
    :type label_regexp: str or None
    :param raw: whether to export the raw images or the normalized ones
    :type raw: bool
    :param writer_cmdline: the happydata writer command-line to use
    :param writer_cmdline: str
    :param rgb: the RGB tuple of integers
    :type rgb: tuple
    :return: None if successful, otherwise error message
    :rtype: str
    """
    result = None

    if datamanager.scan_file is None:
        sample_id = "scan"
    else:
        sample_id = os.path.dirname(datamanager.scan_file)
        if sample_id.endswith("capture"):
            sample_id = os.path.dirname(sample_id)
        sample_id = os.path.basename(sample_id)

    dims = datamanager.dims()
    if len(label_regexp) == 0:
        label_regexp = None
    if label_regexp is None:
        all = datamanager.contours.to_absolute(dims[0], dims[1])
        contours = []
        for l in all:
            contours.extend(l)
    else:
        matches = datamanager.contours.get_contours_regexp(label_regexp)
        contours = [x.to_absolute(dims[0], dims[1]) for x in matches]

    for i, contour in enumerate(contours, start=1):
        datamanager.log("Exporting sub-image #%d: label=%s" % (i, str(contour.label)))

        # configure writer
        try:
            writer = HappyDataWriter.parse_writer(writer_cmdline)
        except:
            result = "Failed to parse writer command-line: %s" % writer_cmdline
            datamanager.log(result)
            return result

        # extract sub-images and export them
        try:
            bbox = contour.bbox()
            data = datamanager.scan_data
            meta = {
                "scan_file": datamanager.scan_file,
                "raw": True,
                "label": contour.label,
                "region": {
                    "top": bbox.top,
                    "left": bbox.left,
                    "bottom": bbox.bottom,
                    "right": bbox.right
                }
            }
            if rgb is not None:
                meta["rgb"] = rgb
            if datamanager.preprocessors_cmdline is not None:
                meta["preprocessors"] = datamanager.preprocessors_cmdline
            wavenumbers = datamanager.get_wavelengths_list()
            if not raw:
                if datamanager.norm_data is None:
                    raw = True
                    wavenumbers = datamanager.get_wavelengths_list()
                    datamanager.log("No normalized data available, using raw instead!")
                else:
                    data = datamanager.norm_data
                    wavenumbers = datamanager.get_wavelengths_norm_list()
                    meta["raw"] = False
                    if datamanager.has_blackref():
                        meta["blackref_locator"] = datamanager.blackref_locator_cmdline
                        meta["blackref_method"] = datamanager.blackref_method_cmdline
                        meta["blackref_file"] = datamanager.blackref_file
                    if datamanager.has_whiteref():
                        meta["whiteref_locator"] = datamanager.whiteref_locator_cmdline
                        meta["whiteref_method"] = datamanager.whiteref_method_cmdline
                        meta["whiteref_file"] = datamanager.whiteref_file
            if wavenumbers is not None:
                meta["wavenumbers"] = wavenumbers
            sub_data = data[bbox.top:bbox.bottom + 1, bbox.left:bbox.right + 1, :]
            happy_data = HappyData(sample_id, contour.label, sub_data, meta, dict(), wavenumbers=wavenumbers)

            # write sub-image
            if isinstance(writer, HappyDataWriterWithNormalization):
                if datamanager.normalization_cmdline != SimpleNormalization().name():
                    writer.normalization(datamanager.normalization_cmdline)
            if isinstance(writer, ImageWriter):
                if rgb is not None:
                    writer.rgb(rgb)
            writer.update_base_dir(path)
            writer.logging_level = "INFO"
            writer.write_data(happy_data)
        except:
            result = "Failed to export sub-image #%d to: %s\n%s" % (i, path, traceback.format_exc())
            datamanager.log(result)

    return result
