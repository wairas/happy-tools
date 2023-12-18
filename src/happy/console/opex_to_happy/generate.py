#!/usr/bin/python3
import argparse
import json
import logging
import os
import shutil
import traceback

import numpy as np
from PIL import Image, ImageDraw
from opex import ObjectPredictions
from spectral import envi

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data import DataManager, HappyData
from happy.data.annotations import locate_opex
from happy.data.black_ref import AbstractBlackReferenceMethod
from happy.data.ref_locator import AbstractReferenceLocator
from happy.data.white_ref import AbstractWhiteReferenceMethod
from happy.writers import HappyWriter

OUTPUT_FORMAT_FLAT = "flat"
OUTPUT_FORMAT_DIRTREE = "dir-tree"
OUTPUT_FORMAT_DIRTREE_WITH_DATA = "dir-tree-with-data"
OUTPUT_FORMATS = [
    OUTPUT_FORMAT_FLAT,
    OUTPUT_FORMAT_DIRTREE,
    OUTPUT_FORMAT_DIRTREE_WITH_DATA,
]


DEFAULT_REGION_ID = "1"


FILENAME_PH_SAMPLEID = "{SAMPLEID}"
""" placeholder for the sample ID in filenames. """

FILENAME_PLACEHOLDERS = [
    FILENAME_PH_SAMPLEID,
]


logger = logging.getLogger("opex2happy")


def log(msg):
    """
    For logging messages.

    :param msg: the message to print
    """
    logger.info(msg)


def get_sample_id(path):
    """
    Returns the sample ID determined from the specified path.

    :param path: the path to get the sample ID from
    :type path: str
    :return: the sample ID
    :rtype: str
    """
    return os.path.splitext(os.path.basename(path))[0]


def envi_to_happy(path_ann, output_dir, datamanager, dry_run=False):
    """
    Converts the envi data into happy format.

    :param path_ann: the path of the annotation JSON file (to locate other data from)
    :type path_ann: str
    :param output_dir: the directory to store the happy data in
    :type output_dir: str
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    """
    logger.info("  --> converting envi to happy format")

    path_hdr = os.path.splitext(path_ann)[0] + ".hdr"
    if not os.path.exists(path_hdr):
        logger.info("    --> not found: %s" % path_hdr)
        return

    logger.info("    --> loading: %s" % path_hdr)

    datamanager.set_scan(path_hdr)
    datamanager.set_annotations(path_ann)
    datamanager.calc_norm_data()

    wavenumbers = None
    wl_dict = datamanager.get_wavelengths()
    if len(wl_dict) > 0:
        wavenumbers = []
        for k in wl_dict:
            wavenumbers.append(wl_dict[k])

    data = HappyData(get_sample_id(path_ann), DEFAULT_REGION_ID, datamanager.norm_data, {}, {}, wavenumbers=wavenumbers)
    if not dry_run:
        logger.info("    --> writing happy data")
        writer = HappyWriter(base_dir=output_dir)
        writer.write_data(data)


def pattern_to_filename(pattern, placeholder_map):
    """
    Replaces placeholders in the provided pattern using the map with the
    relation of placeholder/actual value.

    :param pattern: the pattern string to expand
    :type pattern: str
    :param placeholder_map: the dictionary with the placeholder/actual value mapping
    :type placeholder_map: dict
    :return: the expanded pattern string
    :rtype: str
    """
    result = pattern
    for k in placeholder_map:
        result = result.replace(k, placeholder_map[k])
    return result


def convert(path_ann, path_png, output_dir, datamanager, output_format=OUTPUT_FORMAT_FLAT, labels=None,
            pattern_mask="mask.hdr", pattern_labels="mask.json",
            pattern_png=FILENAME_PH_SAMPLEID + ".png", pattern_annotations=FILENAME_PH_SAMPLEID + ".json",
            no_implicit_background=False, unlabelled=0, include_input=False, dry_run=False):
    """
    Converts the specified file.

    :param path_ann: the OPEX JSON file
    :type path_ann: str
    :param path_png: the PNG image
    :type path_png: str
    :param output_dir: where to store the ENVI data
    :type output_dir: str
    :param output_format: how to store the generated ENVI images
    :type output_format: str
    :param labels: the list of labels to transfer from OPEX into ENVI
    :type labels: list
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
    :param pattern_mask: the file name pattern for the mask
    :type pattern_mask: str
    :param pattern_labels: the file name pattern for the mask label map
    :type pattern_labels: str
    :param pattern_png: the file name pattern for the PNG
    :type pattern_png: str
    :param pattern_annotations: the file name pattern for the OPEX JSON annotations
    :type pattern_annotations: str
    :param no_implicit_background: whether to require explicit annotations for the background or all annotated pixels are considered background (implicit)
    :type no_implicit_background: bool
    :param unlabelled: the value to use for not explicitly labelled pixels
    :type unlabelled: int
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    """
    logger.info("- %s" % path_ann)

    sample_id = os.path.splitext(os.path.basename(path_ann))[0]
    pattern_map = {
        FILENAME_PH_SAMPLEID: sample_id,
    }

    # determine actual output directory
    if output_format == OUTPUT_FORMAT_FLAT:
        output_path = output_dir
    elif (output_format == OUTPUT_FORMAT_DIRTREE) or (output_format == OUTPUT_FORMAT_DIRTREE_WITH_DATA):
        output_path = os.path.join(output_dir, sample_id, DEFAULT_REGION_ID)
    else:
        raise Exception("Unhandled output format: %s" % output_format)
    output_envi = os.path.join(output_path, pattern_to_filename(pattern_mask, pattern_map))
    output_labels = os.path.join(output_path, pattern_to_filename(pattern_labels, pattern_map))
    output_png = os.path.join(output_path, pattern_to_filename(pattern_png, pattern_map))
    output_ann = os.path.join(output_path, pattern_to_filename(pattern_annotations, pattern_map))
    logger.info("  --> output dir: %s" % output_path)

    if output_format == OUTPUT_FORMAT_DIRTREE_WITH_DATA:
        envi_to_happy(path_ann, output_dir, datamanager, dry_run=dry_run)

    # get dimensions
    img = Image.open(path_png)
    width, height = img.size

    # label lookup
    label_map = dict()
    labels_set = set()
    if no_implicit_background:
        label_offset = unlabelled + 1
    else:
        label_offset = 1
    if labels is not None:
        labels_set = set(labels)
        for index, label in enumerate(labels, start=label_offset):
            label_map[label] = index

    # create mask
    img = Image.new("L", (width, height))
    draw = ImageDraw.Draw(img)
    if no_implicit_background:
        draw.rectangle(((0, 0), (width-1, height-1)), fill=unlabelled)
    ann = ObjectPredictions.load_json_from_file(path_ann)
    for obj in ann.objects:
        if (labels is None) or (obj.label in labels_set):
            if obj.label not in label_map:
                label_map[obj.label] = len(label_map) + label_offset
            poly = [tuple(x) for x in obj.polygon.points]
            draw.polygon(poly, fill=label_map[obj.label])

    if not dry_run:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # copy input?
        if include_input:
            logger.info("    --> copying JSON/PNG")
            shutil.copy(path_ann, output_ann)
            shutil.copy(path_png, output_png)

        # label map/wavelengths
        wavelengths = [0]
        if no_implicit_background:
            reverse_label_map = {str(unlabelled): "Unlabelled"}
        else:
            reverse_label_map = {"0": "Background"}
        for k in label_map:
            reverse_label_map[str(label_map[k])] = k
            wavelengths.append(label_map[k])
        logger.info("    --> writing label map: %s" % output_labels)
        with open(output_labels, "w") as fp:
            json.dump(reverse_label_map, fp, indent=2)

        # envi mask
        logger.info("    --> writing envi mask: %s" % output_envi)
        envi.save_image(output_envi, np.array(img), dtype=np.uint8, force=True, interleave='BSQ',
                        metadata={'wavelength': wavelengths})


def generate(input_dirs, output_dir, recursive=False, output_format=OUTPUT_FORMAT_FLAT, labels=None,
             black_ref_locator=None, black_ref_method=None, white_ref_locator=None, white_ref_method=None,
             pattern_mask="mask.hdr", pattern_labels="mask.json",
             pattern_png=FILENAME_PH_SAMPLEID + ".png", pattern_annotations=FILENAME_PH_SAMPLEID + ".json",
             no_implicit_background=False, unlabelled=0, include_input=False, dry_run=False):
    """
    Generates fake RGB images from the HSI images found in the specified directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param output_dir: the (optional) output directory to place the generated PNG images in instead of alongside HSI images
    :type output_dir: str
    :param recursive: whether to look for OPEX files recursively
    :type recursive: bool
    :param output_format: how to store the generated ENVI images
    :type output_format: str
    :param labels: the list of labels to transfer from OPEX into ENVI
    :type labels: list
    :param black_ref_locator: reference locator for black reference files, ignored if None
    :type black_ref_locator: str
    :param black_ref_method: the black reference method to apply, ignored if None
    :type black_ref_method: str
    :param white_ref_locator: reference locator for white reference files, ignored if None
    :type white_ref_locator: str
    :param white_ref_method: the white reference method to apply, ignored if None
    :type white_ref_method: str
    :param pattern_mask: the file name pattern for the mask
    :type pattern_mask: str
    :param pattern_labels: the file name pattern for the mask label map
    :type pattern_labels: str
    :param pattern_png: the file name pattern for the PNG
    :type pattern_png: str
    :param pattern_annotations: the file name pattern for the OPEX JSON annotations
    :type pattern_annotations: str
    :param no_implicit_background: whether to require explicit annotations for the background or all annotated pixels are considered background (implicit)
    :type no_implicit_background: bool
    :param unlabelled: the value to use for not explicitly labelled pixels
    :type unlabelled: int
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    """

    if output_format not in OUTPUT_FORMATS:
        raise Exception("Unknown output format: %s" % output_format)

    # applying black/white ref?
    if output_format == OUTPUT_FORMAT_DIRTREE_WITH_DATA:
        if black_ref_locator is None:
            black_ref_method = None
        if black_ref_method is None:
            black_ref_locator = None
        if white_ref_locator is None:
            white_ref_method = None
        if white_ref_method is None:
            white_ref_locator = None

        if black_ref_locator is not None:
            black_ref_locator = AbstractReferenceLocator.parse_locator(black_ref_locator)
        if black_ref_method is not None:
            black_ref_method = AbstractBlackReferenceMethod.parse_method(black_ref_method)
        if white_ref_locator is not None:
            white_ref_locator = AbstractReferenceLocator.parse_locator(white_ref_locator)
        if white_ref_method is not None:
            white_ref_method = AbstractWhiteReferenceMethod.parse_method(white_ref_method)
    else:
        black_ref_locator = None
        black_ref_method = None
        white_ref_method = None
        white_ref_locator = None

    datamanager = DataManager(log_method=log)
    datamanager.set_blackref_locator(black_ref_locator)
    datamanager.set_blackref_method(black_ref_method)
    datamanager.set_whiteref_locator(white_ref_locator)
    datamanager.set_whiteref_method(white_ref_method)

    ann_paths = []
    locate_opex(input_dirs, ann_paths, recursive=recursive, require_png=True, logger=logger)
    ann_paths = sorted(ann_paths)

    for ann_path in ann_paths:
        img_path = os.path.splitext(ann_path)[0] + ".png"
        convert(ann_path, img_path, output_dir, datamanager, output_format=output_format,
                pattern_mask=pattern_mask, pattern_labels=pattern_labels,
                pattern_png=pattern_png, pattern_annotations=pattern_annotations,
                labels=labels, include_input=include_input,
                no_implicit_background=no_implicit_background, unlabelled=unlabelled,
                dry_run=dry_run)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    init_app()
    parser = argparse.ArgumentParser(
        description="Turns annotations (PNG and OPEX JSON) into Happy ENVI format.",
        prog="happy-opex2happy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the PNG/OPEX files", required=True)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to look for OPEX files recursively", required=False)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("-f", "--output_format", choices=OUTPUT_FORMATS, default=OUTPUT_FORMAT_DIRTREE_WITH_DATA, help="Defines how to store the data in the output directory.", required=True)
    parser.add_argument("-l", "--labels", type=str, help="The comma-separated list of object labels to export ('Background' is automatically added).", required=True)
    parser.add_argument("-N", "--no_implicit_background", action="store_true", help="whether to require explicit annotations for the background rather than assuming all un-annotated pixels are background", required=False)
    parser.add_argument("-u", "--unlabelled", type=int, default=0, help="The value to use for pixels that do not have an explicit annotation (label values start after this value)", required=False)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--pattern_mask", metavar="PATTERN", help="the pattern to use for saving the mask ENVI file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default="mask.hdr", required=False)
    parser.add_argument("--pattern_labels", metavar="PATTERN", help="the pattern to use for saving the label map for the mask ENVI file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default="mask.json", required=False)
    parser.add_argument("--pattern_png", metavar="PATTERN", help="the pattern to use for saving the mask PNG file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default=FILENAME_PH_SAMPLEID + ".png", required=False)
    parser.add_argument("--pattern_annotations", metavar="PATTERN", help="the pattern to use for saving the OPEX JSON annotation file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default=FILENAME_PH_SAMPLEID + ".json", required=False)
    parser.add_argument("-I", "--include_input", action="store_true", help="whether to copy the PNG/JSON file across to the output dir", required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit generating any data or creating directories", required=False)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)
    set_logging_level(logger, parsed.logging_level)
    generate(parsed.input_dir, parsed.output_dir,
             recursive=parsed.recursive, output_format=parsed.output_format, labels=parsed.labels.split(","),
             black_ref_locator=parsed.black_ref_locator, black_ref_method=parsed.black_ref_method,
             white_ref_locator=parsed.white_ref_locator, white_ref_method=parsed.white_ref_method,
             pattern_mask=parsed.pattern_mask, pattern_labels=parsed.pattern_labels,
             pattern_png=parsed.pattern_png, pattern_annotations=parsed.pattern_annotations,
             no_implicit_background=parsed.no_implicit_background, unlabelled=parsed.unlabelled,
             include_input=parsed.include_input, dry_run=parsed.dry_run)


def sys_main() -> int:
    """
    Runs the main function using the system cli arguments, and
    returns a system error code.

    :return: 0 for success, 1 for failure.
    """
    try:
        main()
        return 0
    except Exception:
        print(traceback.format_exc())
        return 1


if __name__ == '__main__':
    main()
