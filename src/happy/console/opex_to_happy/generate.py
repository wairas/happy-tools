#!/usr/bin/python3
import argparse
import json
import os
import shutil
import traceback

import numpy as np
from spectral import envi
import spectral.io.envi as envi_load
from PIL import Image, ImageDraw
from opex import ObjectPredictions
from happy.data import HappyData, configure_envi_settings
from happy.writers import HappyWriter
from happy.data.ref_locator import AbstractReferenceLocator, AbstractFileBasedReferenceLocator
from happy.data.white_ref import AbstractWhiteReferenceMethod
from happy.data.black_ref import AbstractBlackReferenceMethod

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


def locate_opex(input_dirs, recursive, verbose, opex_files):
    """
    Locates the PNG/OPEX JSON pairs.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param recursive: whether to look for OPEX files recursively
    :type recursive: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    :param opex_files: for collecting the OPEX JSON files
    :type opex_files: list
    """
    if isinstance(input_dirs, str):
        input_dirs = [input_dirs]

    for input_dir in input_dirs:
        if verbose:
            print("Entering: %s" % input_dir)

        for f in os.listdir(input_dir):
            full = os.path.join(input_dir, f)

            # directory?
            if os.path.isdir(full):
                if recursive:
                    locate_opex(full, recursive, verbose, opex_files)
                    if verbose:
                        print("Back in: %s" % input_dir)
                else:
                    continue

            if not f.lower().endswith(".json"):
                continue

            ann_path = os.path.join(input_dir, f)
            prefix = os.path.splitext(ann_path)[0]
            img_path = prefix + ".png"
            if not os.path.exists(img_path):
                if verbose:
                    print("No annotation JSON/PNG pair for: %s" % (prefix + ".*"))
                continue
            else:
                opex_files.append(ann_path)


def get_sample_id(path):
    """
    Returns the sample ID determined from the specified path.

    :param path: the path to get the sample ID from
    :type path: str
    :return: the sample ID
    :rtype: str
    """
    return os.path.splitext(os.path.basename(path))[0]


def envi_to_happy(path_ann, output_dir, black_ref_locator=None, black_ref_method=None,
                  white_ref_locator=None, white_ref_method=None, dry_run=False, verbose=False):
    """
    Converts the envi data into happy format.

    :param path_ann: the path of the annotation JSON file (to locate other data from)
    :type path_ann: str
    :param output_dir: the directory to store the happy data in
    :type output_dir: str
    :param black_ref_locator: reference locator for black reference files, ignored if None
    :type black_ref_locator: AbstractReferenceLocator
    :param black_ref_method: the black reference method to apply, ignored if None
    :type black_ref_method: AbstractBlackReferenceMethod
    :param white_ref_locator: reference locator for white reference files, ignored if None
    :type white_ref_locator: AbstractReferenceLocator
    :param white_ref_method: the white reference method to apply, ignored if None
    :type white_ref_method: AbstractWhiteReferenceMethod
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    """
    if verbose:
        print("  --> converting envi to happy format")

    path_hdr = os.path.splitext(path_ann)[0] + ".hdr"
    if not os.path.exists(path_hdr):
        print("    --> not found: %s" % path_hdr)
        return

    if verbose:
        print("    --> loading: %s" % path_hdr)
    scan = envi_load.open(path_hdr).load()

    if black_ref_locator is not None:
        if isinstance(black_ref_locator, AbstractFileBasedReferenceLocator):
            black_ref_locator.base_file = path_hdr
            black_ref_file = black_ref_locator.locate()
            if black_ref_file is not None:
                if os.path.exists(black_ref_file):
                    if verbose:
                        print("    --> loading black ref: %s" % black_ref_file)
                    black_ref = envi_load.open(path_hdr).load()
                    black_ref_method.reference = black_ref
                    scan = black_ref_method.apply(scan)
                else:
                    print("    --> black ref file not found: %s" % black_ref_file)
        else:
            black_ref = black_ref_locator.locate()
            black_ref_method.reference = black_ref
            scan = black_ref_method.apply(scan)

    if white_ref_locator is not None:
        if isinstance(white_ref_locator, AbstractFileBasedReferenceLocator):
            white_ref_locator.base_file = path_hdr
            white_ref_file = white_ref_locator.locate()
            if white_ref_file is not None:
                if os.path.exists(white_ref_file):
                    if verbose:
                        print("    --> loading white ref: %s" % white_ref_file)
                    white_ref = envi_load.open(path_hdr).load()
                    white_ref_method.reference = white_ref
                    scan = white_ref_method.apply(scan)
            else:
                print("    --> white ref file not found: %s" % white_ref_file)
        else:
            white_ref = white_ref_locator.locate()
            white_ref_method.reference = white_ref
            scan = white_ref_method.apply(scan)

    data = HappyData(get_sample_id(path_ann), DEFAULT_REGION_ID, scan, {}, {})
    if not dry_run:
        if verbose:
            print("    --> writing happy data")
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


def convert(path_ann, path_png, output_dir, output_format=OUTPUT_FORMAT_FLAT, labels=None,
            black_ref_locator=None, black_ref_method=None, white_ref_locator=None, white_ref_method=None,
            pattern_mask="mask.hdr", pattern_labels="mask.json",
            pattern_png=FILENAME_PH_SAMPLEID + ".png", pattern_annotations=FILENAME_PH_SAMPLEID + ".json",
            include_input=False, dry_run=False, verbose=False):
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
    :param black_ref_locator: reference locator for black reference files, ignored if None
    :type black_ref_locator: AbstractReferenceLocator
    :param black_ref_method: the black reference method to apply, ignored if None
    :type black_ref_method: AbstractBlackReferenceMethod
    :param white_ref_locator: reference locator for white reference files, ignored if None
    :type white_ref_locator: AbstractReferenceLocator
    :param white_ref_method: the white reference method to apply, ignored if None
    :type white_ref_method: AbstractWhiteReferenceMethod
    :param pattern_mask: the file name pattern for the mask
    :type pattern_mask: str
    :param pattern_labels: the file name pattern for the mask label map
    :type pattern_labels: str
    :param pattern_png: the file name pattern for the PNG
    :type pattern_png: str
    :param pattern_annotations: the file name pattern for the OPEX JSON annotations
    :type pattern_annotations: str
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving data/creating dirs
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    """
    if verbose:
        print("- %s" % path_ann)

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
    if verbose:
        print("  --> output dir: %s" % output_path)

    if output_format == OUTPUT_FORMAT_DIRTREE_WITH_DATA:
        envi_to_happy(path_ann, output_dir,
                      black_ref_locator=black_ref_locator, black_ref_method=black_ref_method,
                      white_ref_locator=white_ref_locator, white_ref_method=white_ref_method,
                      dry_run=dry_run, verbose=verbose)

    # get dimensions
    img = Image.open(path_png)
    width, height = img.size

    # label lookup
    label_map = dict()
    labels_set = set()
    if labels is not None:
        labels_set = set(labels)
        for index, label in enumerate(labels, start=1):
            label_map[label] = index

    # create mask
    img = Image.new("L", (width, height))
    draw = ImageDraw.Draw(img)
    ann = ObjectPredictions.load_json_from_file(path_ann)
    for obj in ann.objects:
        if (labels is None) or (obj.label in labels_set):
            if obj.label not in label_map:
                label_map[obj.label] = len(label_map) + 1
            poly = [tuple(x) for x in obj.polygon.points]
            draw.polygon(poly, fill=label_map[obj.label])

    if not dry_run:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # copy input?
        if include_input:
            if verbose:
                print("    --> copying JSON/PNG")
            shutil.copy(path_ann, output_ann)
            shutil.copy(path_png, output_png)

        # label map/wavelengths
        wavelengths = [0]
        reverse_label_map = {"0": "Background"}
        for k in label_map:
            reverse_label_map[str(label_map[k])] = k
            wavelengths.append(label_map[k])
        if verbose:
            print("    --> writing label map: %s" % output_labels)
        with open(output_labels, "w") as fp:
            json.dump(reverse_label_map, fp, indent=2)

        # envi mask
        if verbose:
            print("    --> writing envi mask: %s" % output_envi)
        envi.save_image(output_envi, np.array(img), dtype=np.uint8, force=True, interleave='BSQ',
                        metadata={'wavelength': wavelengths})


def generate(input_dirs, output_dir, recursive=False, output_format=OUTPUT_FORMAT_FLAT, labels=None,
             black_ref_locator=None, black_ref_method=None, white_ref_locator=None, white_ref_method=None,
             pattern_mask="mask.hdr", pattern_labels="mask.json",
             pattern_png=FILENAME_PH_SAMPLEID + ".png", pattern_annotations=FILENAME_PH_SAMPLEID + ".json",
             include_input=False, dry_run=False, verbose=False):
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
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
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

    ann_paths = []
    locate_opex(input_dirs, recursive, verbose, ann_paths)

    for ann_path in ann_paths:
        img_path = os.path.splitext(ann_path)[0] + ".png"
        convert(ann_path, img_path, output_dir=output_dir, output_format=output_format,
                black_ref_locator=black_ref_locator, black_ref_method=black_ref_method,
                white_ref_locator=white_ref_locator, white_ref_method=white_ref_method,
                pattern_mask=pattern_mask, pattern_labels=pattern_labels,
                pattern_png=pattern_png, pattern_annotations=pattern_annotations,
                labels=labels, include_input=include_input, dry_run=dry_run, verbose=verbose)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    configure_envi_settings()
    parser = argparse.ArgumentParser(
        description="Turns annotations (PNG and OPEX JSON) into Happy ENVI format.",
        prog="happy-opex2happy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the PNG/OPEX files", required=True)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to look for OPEX files recursively", required=False)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("-f", "--output_format", choices=OUTPUT_FORMATS, default=OUTPUT_FORMAT_DIRTREE_WITH_DATA, help="Defines how to store the data in the output directory.", required=True)
    parser.add_argument("-l", "--labels", type=str, help="The comma-separated list of object labels to export ('Background' is automatically added).", required=True)
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
    parser.add_argument("-v", "--verbose", action="store_true", help="whether to be more verbose with the output", required=False)
    parsed = parser.parse_args(args=args)
    generate(parsed.input_dir, parsed.output_dir,
             recursive=parsed.recursive, output_format=parsed.output_format, labels=parsed.labels.split(","),
             black_ref_locator=parsed.black_ref_locator, black_ref_method=parsed.black_ref_method,
             white_ref_locator=parsed.white_ref_locator, white_ref_method=parsed.white_ref_method,
             pattern_mask=parsed.pattern_mask, pattern_labels=parsed.pattern_labels,
             pattern_png=parsed.pattern_png, pattern_annotations=parsed.pattern_annotations,
             include_input=parsed.include_input, dry_run=parsed.dry_run, verbose=parsed.verbose)


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
