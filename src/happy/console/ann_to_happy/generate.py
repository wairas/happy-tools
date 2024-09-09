#!/usr/bin/python3
import argparse
import json
import logging
import os
import re
import shutil
import traceback

import numpy as np
from PIL import Image, ImageDraw
from opex import ObjectPredictions
from spectral import envi

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data import DataManager, HappyData, LABEL_WHITEREF
from happy.data.annotations import locate_annotations, AnnotationFiles, load_label_map, MASK_PREFIX
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


CONVERSION_PIXELS = "pixels"
CONVERSION_POLYGONS = "polygons"
CONVERSION_PIXELS_THEN_POLYGONS = "pixels_then_polygons"
CONVERSION_POLYGONS_THEN_PIXELS = "polygons_then_pixels"
CONVERSIONS = [
    CONVERSION_PIXELS,
    CONVERSION_POLYGONS,
    CONVERSION_PIXELS_THEN_POLYGONS,
    CONVERSION_POLYGONS_THEN_PIXELS,
]


logger = logging.getLogger("ann2happy")


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


def envi_to_happy(cont_ann: AnnotationFiles, output_dir, datamanager, dry_run=False):
    """
    Converts the envi data into happy format.

    :param cont_ann: the path of the annotation JSON file (to locate other data from)
    :type cont_ann: AnnotationFiles
    :param output_dir: the directory to store the happy data in
    :type output_dir: str
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    """
    logger.info("Converting envi to happy format")

    path_scan = os.path.splitext(cont_ann.png)[0] + ".hdr"
    if not os.path.exists(path_scan):
        logger.info("Not found: %s" % path_scan)
        return

    logger.info("Loading: %s" % path_scan)

    datamanager.load_scan(path_scan)
    datamanager.load_contours(cont_ann.opex)
    datamanager.calc_norm_data()

    wavenumbers = datamanager.get_wavelengths_norm_list()
    sample_id = get_sample_id(cont_ann.png)
    data = HappyData(sample_id, DEFAULT_REGION_ID, datamanager.norm_data, {}, {}, wavenumbers=wavenumbers)
    if not dry_run:
        logger.info("Writing happy data: %s --> %s" % (output_dir, sample_id))
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


def remap_indices(envi_ann, indices_old, indices_new):
    """
    Remaps the pixels in the pixel annotations.

    :param envi_ann: the pixel annotations to update
    :param indices_old: the list of old int indices
    :type indices_old: list
    :param indices_new: the list of new int indices
    :type indices_new: list
    """
    for index_old in indices_old:
        envi_ann = np.where(envi_ann == index_old, -index_old, envi_ann)
    for i in range(len(indices_old)):
        envi_ann = np.where(envi_ann == -indices_old[i], indices_new[i], envi_ann)


def remap_pixel_annotations(ann, label_map, envi_label_map):
    """
    Remaps the ENVI pixel annotations in case the label maps differ.

    :param ann: the pixel annotations to remap
    :param label_map: the user-provided label map
    :type label_map: dict
    :param envi_label_map: the label map associated with the pixel annotations
    :type envi_label_map: dict
    :return: the potentially updated pixel annotations, 255 = to ignore
    """
    missing = []
    # check whether labels present
    for label in envi_label_map.values():
        if label not in label_map:
            missing.append(label)
            logger.warning("ENVI label not among user-supplied labels: %s" % label)

    # create reverse lookup
    reverse_envi_label_map = dict()
    for index_str in envi_label_map:
        reverse_envi_label_map[envi_label_map[index_str]] = int(index_str)

    # check if label indices differ
    differ = dict()
    for label in label_map:
        if label in reverse_envi_label_map:
            if label_map[label] != reverse_envi_label_map[label]:
                differ[reverse_envi_label_map[label]] = label_map[label]

    # remove missing labels
    if len(missing) > 0:
        for k in envi_label_map:
            i = int(k)
            if envi_label_map[k] in missing:
                logger.warning("Removing label: %s" % envi_label_map[k])
                ann = np.where(ann == i, 0, ann)

    # check for undefined indices -> 255 (to be ignored)
    all_indices = set(np.unique(ann))
    for index_str in envi_label_map:
        index = int(index_str)
        all_indices.remove(index)
    if len(all_indices) > 0:
        for index in all_indices:
            # 0 is default value when initializing pixel annotations, no need to warn about it
            if index > 0:
                logger.warning("Ignoring pixel annotation index: %d" % index)
            ann = np.where(ann == index, 255, ann)

    # remap indices
    if len(differ) > 0:
        # move into negative space
        for old in differ:
            if old == 0:
                new = -254
            else:
                new = -old
            ann = np.where(ann == old, new, ann)
        # move into current user-label space
        for old, new in differ.items():
            if old == 0:
                old = -254
            else:
                old = -old
            ann = np.where(ann == old, new, ann)

    ann = ann.astype(np.uint8)

    return ann


def apply_envi(cont_ann: AnnotationFiles, img: np.ndarray, label_map: dict) -> np.ndarray:
    """
    Applies the pixel annotations.

    :param cont_ann: the annotation container
    :type cont_ann: AnnotationFiles
    :param img: the numpy array to overlay the annotations onto
    :type img: np.ndarray
    :param label_map: the label map to use
    :type label_map: str
    :return: the updated image
    :rtype: np.ndarray
    """
    if cont_ann.envi_mask is not None:
        logger.info("Applying ENVI pixel annotations...")
        envi_ann = envi.open(cont_ann.envi_mask).load()
        envi_ann = envi_ann.squeeze().astype(np.uint8)
        envi_label_map = None
        envi_label_map_path = os.path.splitext(cont_ann.envi_mask)[0] + ".json"
        if os.path.exists(envi_label_map_path):
            envi_label_map, msg = load_label_map(envi_label_map_path)
            if msg is not None:
                logger.error(msg)
        # remap indices, if necessary
        if envi_label_map is None:
            logger.warning("No label map available for: %s" % cont_ann.envi_mask)
        else:
            envi_ann = remap_pixel_annotations(envi_ann, label_map, envi_label_map)
        np.copyto(img, envi_ann, where=(envi_ann > 0) & (envi_ann < 255))
    else:
        logger.warning("No ENVI pixel annotations, skipping!")
    return img


def apply_opex(cont_ann: AnnotationFiles, img: np.ndarray, label_map: dict, labels_set: set) -> np.ndarray:
    """
    Applies the polygon annotations.

    :param cont_ann: the annotation container
    :type cont_ann: AnnotationFiles
    :param img: the numpy array to overlay the annotations onto
    :type img: np.ndarray
    :param label_map: the label map to use
    :type label_map: str
    :param labels_set: the labels set, none if user supplied no labels
    :type labels_set: set
    :return: the updated image
    :rtype: np.ndarray
    """
    if cont_ann.opex is not None:
        ann = ObjectPredictions.load_json_from_file(cont_ann.opex)
        if len(ann.objects) > 0:
            logger.info("Applying OPEX polygon annotations...")
            pimg = Image.fromarray(img, "L")
            draw = ImageDraw.Draw(pimg)
            for obj in ann.objects:
                if (labels_set is None) or (obj.label in labels_set):
                    if obj.label not in label_map:
                        logger.warning("Skipping object with label %s: %s" % (obj.label, str(obj)))
                        continue
                    poly = [tuple(x) for x in obj.polygon.points]
                    draw.polygon(poly, fill=label_map[obj.label])
            img = np.asarray(pimg, dtype=np.uint8)
        else:
            logger.warning("OPEX annotations are empty, nothing to do.")
    else:
        logger.warning("No OPEX polygon annotations, skipping!")
    return img


def convert(cont_ann: AnnotationFiles, output_dir: str, datamanager: DataManager,
            conversion=CONVERSION_PIXELS_THEN_POLYGONS, output_format: str = OUTPUT_FORMAT_FLAT, labels=None,
            pattern_mask: str = "mask.hdr",
            pattern_labels: str = "mask.json",
            pattern_png: str = FILENAME_PH_SAMPLEID + ".png",
            pattern_opex: str = FILENAME_PH_SAMPLEID + ".json",
            pattern_envi: str = MASK_PREFIX + FILENAME_PH_SAMPLEID + ".hdr",
            no_implicit_background=False, unlabelled=0, include_input=False, dry_run=False):
    """
    Converts the specified file.

    :param cont_ann: the container with the annotation files
    :param output_dir: where to store the ENVI data
    :type cont_ann: str
    :type output_dir: str
    :param conversion: what annotations and in what order to apply
    :type conversion: str
    :param output_format: how to store the generated ENVI images
    :type output_format: str
    :param labels: the list of labels to transfer from OPEX into ENVI
    :type labels: list
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
    :param pattern_mask: the file name pattern for the mask (output)
    :type pattern_mask: str
    :param pattern_labels: the file name pattern for the mask label map (output)
    :type pattern_labels: str
    :param pattern_png: the file name pattern for the PNG (output)
    :type pattern_png: str
    :param pattern_opex: the file name pattern for the OPEX JSON annotations (output)
    :type pattern_opex: str
    :param pattern_envi: the file name pattern for the ENVI mask annotations (output)
    :type pattern_envi: str
    :param no_implicit_background: whether to require explicit annotations for the background or all annotated pixels are considered background (implicit)
    :type no_implicit_background: bool
    :param unlabelled: the value to use for not explicitly labelled pixels
    :type unlabelled: int
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    """
    logger.info("Conversion input: %s" % cont_ann)

    sample_id = os.path.splitext(os.path.basename(cont_ann.png))[0]
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
    output_mask = os.path.join(output_path, pattern_to_filename(pattern_mask, pattern_map))
    output_labels = os.path.join(output_path, pattern_to_filename(pattern_labels, pattern_map))
    output_png = os.path.join(output_path, pattern_to_filename(pattern_png, pattern_map))
    output_opex = os.path.join(output_path, pattern_to_filename(pattern_opex, pattern_map))
    output_envi = os.path.join(output_path, pattern_to_filename(pattern_envi, pattern_map))
    logger.info("Output dir: %s" % output_path)

    if output_format == OUTPUT_FORMAT_DIRTREE_WITH_DATA:
        envi_to_happy(cont_ann, output_dir, datamanager, dry_run=dry_run)

    # get dimensions
    img = Image.open(cont_ann.png)
    width, height = img.size

    # label lookup
    label_map = dict()
    labels_set = None
    if no_implicit_background:
        label_offset = unlabelled + 1
    else:
        label_offset = 1
    if labels is not None:
        labels_set = set(labels)
        for index, label in enumerate(labels, start=label_offset):
            label_map[label] = index

    # create base image
    img = np.zeros((height, width), dtype=np.uint8)
    if no_implicit_background:
        img.fill(unlabelled)

    # apply
    if conversion == CONVERSION_PIXELS:
        img = apply_envi(cont_ann, img, label_map)
    elif conversion == CONVERSION_POLYGONS:
        img = apply_opex(cont_ann, img, label_map, labels_set)
    elif conversion == CONVERSION_PIXELS_THEN_POLYGONS:
        img = apply_envi(cont_ann, img, label_map)
        img = apply_opex(cont_ann, img, label_map, labels_set)
    elif conversion == CONVERSION_POLYGONS_THEN_PIXELS:
        img = apply_opex(cont_ann, img, label_map, labels_set)
        img = apply_envi(cont_ann, img, label_map)
    else:
        raise Exception("Unsupported conversion: %s" % conversion)

    if not dry_run:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # copy input?
        if include_input:
            logger.info("Copying JSON/PNG/ENVI")
            shutil.copy(cont_ann.opex, output_opex)
            shutil.copy(cont_ann.png, output_png)
            if cont_ann.envi_mask is not None:
                shutil.copy(cont_ann.envi_mask, output_envi)

        # label map/wavelengths
        wavelengths = [0]
        if no_implicit_background:
            reverse_label_map = {str(unlabelled): "Unlabelled"}
        else:
            reverse_label_map = {"0": "Background"}
        for k in label_map:
            reverse_label_map[str(label_map[k])] = k
            wavelengths.append(label_map[k])
        logger.info("Writing label map: %s" % output_labels)
        with open(output_labels, "w") as fp:
            json.dump(reverse_label_map, fp, indent=2)

        # envi mask
        logger.info("Writing envi mask: %s" % output_mask)
        envi.save_image(output_mask, np.array(img), dtype=np.uint8, force=True, interleave='BSQ',
                        metadata={'wavelength': wavelengths})


def generate(input_dirs, output_dir, regexp=None, conversion=CONVERSION_PIXELS_THEN_POLYGONS, recursive=False,
             output_format=OUTPUT_FORMAT_FLAT, labels=None, black_ref_locator=None, black_ref_method=None,
             white_ref_locator=None, white_ref_method=None, white_ref_annotations=None,
             black_ref_locator_for_white_ref=None, black_ref_method_for_white_ref=None,
             pattern_mask="mask.hdr", pattern_labels="mask.json",
             pattern_png=FILENAME_PH_SAMPLEID + ".png", pattern_opex=FILENAME_PH_SAMPLEID + ".json",
             pattern_envi=MASK_PREFIX + FILENAME_PH_SAMPLEID + ".hdr", no_implicit_background=False, unlabelled=0,
             include_input=False, dry_run=False, resume_from=None):
    """
    Generates fake RGB images from the HSI images found in the specified directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param output_dir: the (optional) output directory to place the generated PNG images in instead of alongside HSI images
    :type output_dir: str
    :param regexp: the regular expression to match against the ENVI base name, e.g., for processing subset
    :type regexp: str or None
    :param conversion: what annotations and in what order to apply
    :type conversion: str
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
    :param white_ref_annotations: the OPEX JSON file with the annotated white ref if it cannot be determined automatically
    :type white_ref_annotations: str
    :param black_ref_locator_for_white_ref: the black reference locator to use for finding the black ref data to apply to the white reference scan
    :type black_ref_locator_for_white_ref: str
    :param black_ref_method_for_white_ref: the black reference method to use for applying the black ref data to the white reference scan
    :type black_ref_method_for_white_ref: str
    :param pattern_mask: the file name pattern for the mask (output)
    :type pattern_mask: str
    :param pattern_labels: the file name pattern for the mask label map (output)
    :type pattern_labels: str
    :param pattern_png: the file name pattern for the PNG (output)
    :type pattern_png: str
    :param pattern_opex: the file name pattern for the OPEX JSON annotations (output)
    :type pattern_opex: str
    :param pattern_envi: the file name pattern for the ENVI mask annotations (output)
    :type pattern_envi: str
    :param no_implicit_background: whether to require explicit annotations for the background or all annotated pixels are considered background (implicit)
    :type no_implicit_background: bool
    :param unlabelled: the value to use for not explicitly labelled pixels
    :type unlabelled: int
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param resume_from: the directory to resume the processing from (determined dirs preceding this one will get skipped), ignored if None
    :type resume_from: str
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
        if black_ref_method_for_white_ref is None:
            black_ref_locator_for_white_ref = None
        # annotations defined for white ref?
        whiteref_ann = None
        if white_ref_annotations is not None:
            if os.path.exists(white_ref_annotations):
                preds = ObjectPredictions.load_json_from_file(white_ref_annotations)
                whiteref_obj = None
                for obj in preds.objects:
                    if obj.label == LABEL_WHITEREF:
                        whiteref_obj = obj
                        break
                if whiteref_obj is None:
                    logger.warning(
                        "Failed to locate label %s in OPEX JSON file: %s" % (LABEL_WHITEREF, white_ref_annotations))
                else:
                    whiteref_ann = (whiteref_obj.bbox.top, whiteref_obj.bbox.left, whiteref_obj.bbox.bottom,
                                    whiteref_obj.bbox.right)
            else:
                logger.warning("OPEX JSON file not found (white ref annotations): %s" % white_ref_annotations)
    else:
        black_ref_locator = None
        black_ref_method = None
        white_ref_method = None
        white_ref_locator = None
        black_ref_locator_for_white_ref = None
        whiteref_ann = None

    datamanager = DataManager(log_method=log)
    datamanager.set_blackref_locator(black_ref_locator)
    datamanager.set_blackref_method(black_ref_method)
    datamanager.set_whiteref_locator(white_ref_locator)
    datamanager.set_whiteref_method(white_ref_method)
    datamanager.set_blackref_locator_for_whiteref(black_ref_locator_for_white_ref)
    datamanager.set_blackref_method_for_whiteref(black_ref_method_for_white_ref)
    if whiteref_ann is not None:
        datamanager.set_whiteref_annotation(whiteref_ann, False)

    ann_conts = []
    locate_annotations(input_dirs, ann_conts, recursive=recursive, require_png=True, require_opex_or_envi=True, logger=logger)
    ann_conts = sorted(ann_conts)
    logger.info("# files located: %d" % len(ann_conts))

    # subset?
    if (regexp is not None) and (len(regexp) > 0):
        _ann_conts = []
        for ann_cont in ann_conts:
            if re.search(regexp, ann_cont.base) is not None:
                _ann_conts.append(ann_cont)
        ann_conts = _ann_conts
        logger.info("# files that match %s: %d" % (regexp, len(ann_conts)))

    # process only subset?
    if resume_from is not None:
        _ann_conts = []
        found = False
        for ann_path in ann_conts:
            ann_dir = os.path.dirname(ann_path)
            if ann_dir.startswith(resume_from):
                found = True
            if found:
                _ann_conts.append(ann_path)
        if len(_ann_conts) == 0:
            raise Exception("Resuming from dir '%s' resulted in an empty set of annotations to process!" % resume_from)
        else:
            logger.info("Resume from dir '%s' changed number of annotations to process from %d to %d." % (resume_from, len(ann_conts), len(_ann_conts)))
        ann_conts = _ann_conts
        logger.info("# files to resume from %s: %d" % (resume_from, len(ann_conts)))

    for i, ann_path in enumerate(ann_conts, start=1):
        logger.info("Converting %d/%d..." % (i, len(ann_conts)))
        convert(ann_path, output_dir, datamanager, conversion=conversion, output_format=output_format,
                pattern_mask=pattern_mask, pattern_labels=pattern_labels,
                pattern_png=pattern_png, pattern_opex=pattern_opex, pattern_envi=pattern_envi,
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
        description="Turns annotations (PNG, OPEX JSON, ENVI pixel annotations) into Happy ENVI format.",
        prog="happy-ann2happy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the PNG/OPEX/ENVI files", required=True)
    parser.add_argument("--regexp", type=str, metavar="REGEXP", help="The regexp for matching the ENVI base files (name only), e.g., for selecting a subset.", required=False, default=None)
    parser.add_argument("-c", "--conversion", choices=CONVERSIONS, default=CONVERSION_PIXELS_THEN_POLYGONS, help="What annotations and in what order to apply (subsequent overlays can overwrite annotations).", required=False)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to look for OPEX/ENVI files recursively", required=False)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("-f", "--output_format", choices=OUTPUT_FORMATS, default=OUTPUT_FORMAT_DIRTREE_WITH_DATA, help="Defines how to store the data in the output directory.", required=True)
    parser.add_argument("-l", "--labels", type=str, help="The comma-separated list of object labels to export ('Background' is automatically added).", required=True)
    parser.add_argument("-N", "--no_implicit_background", action="store_true", help="whether to require explicit annotations for the background rather than assuming all un-annotated pixels are background", required=False)
    parser.add_argument("-u", "--unlabelled", type=int, default=0, help="The value to use for pixels that do not have an explicit annotation (label values start after this value)", required=False)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size; requires: " + OUTPUT_FORMAT_DIRTREE_WITH_DATA, default=None, required=False)
    parser.add_argument("--white_ref_annotations", metavar="FILE", help="the OPEX JSON file with the annotated white reference if it cannot be determined automatically", default=None, required=False)
    parser.add_argument("--black_ref_locator_for_white_ref", metavar="LOCATOR", help="the reference locator scheme to use for locating black references that get applied to the white reference, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method_for_white_ref", metavar="METHOD", help="the black reference method to use for applying black references to the white reference, eg br-same-size", default=None, required=False)
    parser.add_argument("--pattern_mask", metavar="PATTERN", help="the pattern to use for saving the mask ENVI file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default="mask.hdr", required=False)
    parser.add_argument("--pattern_labels", metavar="PATTERN", help="the pattern to use for saving the label map for the mask ENVI file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default="mask.json", required=False)
    parser.add_argument("--pattern_png", metavar="PATTERN", help="the pattern to use for saving the mask PNG file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default=FILENAME_PH_SAMPLEID + ".png", required=False)
    parser.add_argument("--pattern_opex", metavar="PATTERN", help="the pattern to use for saving the OPEX JSON annotation file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default=FILENAME_PH_SAMPLEID + ".json", required=False)
    parser.add_argument("--pattern_envi", metavar="PATTERN", help="the pattern to use for saving the ENVI mask annotation file, available placeholders: " + ",".join(FILENAME_PLACEHOLDERS), default=MASK_PREFIX + FILENAME_PH_SAMPLEID + ".hdr", required=False)
    parser.add_argument("-I", "--include_input", action="store_true", help="whether to copy the PNG/JSON file across to the output dir", required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit generating any data or creating directories", required=False)
    parser.add_argument("--resume_from", metavar="DIR", type=str, help="The directory to restart the processing with (all determined dirs preceding this one get skipped)", required=False, default=None)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)
    set_logging_level(logger, parsed.logging_level)
    generate(parsed.input_dir, parsed.output_dir, regexp=parsed.regexp, conversion=parsed.conversion,
             recursive=parsed.recursive, output_format=parsed.output_format, labels=parsed.labels.split(","),
             black_ref_locator=parsed.black_ref_locator, black_ref_method=parsed.black_ref_method,
             white_ref_locator=parsed.white_ref_locator, white_ref_method=parsed.white_ref_method,
             white_ref_annotations=parsed.white_ref_annotations,
             black_ref_locator_for_white_ref=parsed.black_ref_locator_for_white_ref,
             black_ref_method_for_white_ref=parsed.black_ref_method_for_white_ref,
             pattern_mask=parsed.pattern_mask, pattern_labels=parsed.pattern_labels,
             pattern_png=parsed.pattern_png, pattern_opex=parsed.pattern_opex, pattern_envi=parsed.pattern_envi,
             no_implicit_background=parsed.no_implicit_background, unlabelled=parsed.unlabelled,
             include_input=parsed.include_input, dry_run=parsed.dry_run, resume_from=parsed.resume_from)


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
