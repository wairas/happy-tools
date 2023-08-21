#!/usr/bin/python3
import argparse
import json
import os
import shutil
import traceback

import numpy as np
from spectral import envi
from PIL import Image, ImageDraw
from opex import ObjectPredictions

OUTPUT_FORMAT_FLAT = "flat"
OUTPUT_FORMAT_DIRTREE = "dir-tree"
OUTPUT_FORMATS = [
    OUTPUT_FORMAT_FLAT,
    OUTPUT_FORMAT_DIRTREE,
]


def convert(path_png, path_ann, output_dir, output_format=OUTPUT_FORMAT_FLAT, labels=None,
            include_input=False, dry_run=False, verbose=False):
    """
    Converts the specified file.

    :param path_png: the PNG image
    :type path_png: str
    :param path_ann: the OPEX JSON file
    :type path_ann: str
    :param output_dir: where to store the ENVI data
    :type output_dir: str
    :param output_format: how to store the generated ENVI images
    :type output_format: str
    :param labels: the list of labels to transfer from OPEX into ENVI
    :type labels: list
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    """
    if verbose:
        print("- %s" % path_png)

    # determine actual output directory
    sample_id = os.path.splitext(os.path.basename(path_png))[0]
    if output_format == OUTPUT_FORMAT_FLAT:
        output_path = output_dir
        # output files
        output_envi = os.path.join(output_path, sample_id + ".hdr")
        output_png = os.path.join(output_path, sample_id + ".png")
        output_ann = os.path.join(output_path, sample_id + ".json")
        output_labels = os.path.join(output_path, sample_id + "-labels.json")
    elif output_format == OUTPUT_FORMAT_DIRTREE:
        output_path = os.path.join(output_dir, sample_id, "1")
        # output files
        output_envi = os.path.join(output_path, "mask.hdr")
        output_png = os.path.join(output_path, sample_id + ".png")
        output_ann = os.path.join(output_path, sample_id + ".json")
        output_labels = os.path.join(output_path, "labels.json")
    else:
        raise Exception("Unhandled output format: %s" % output_format)

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

    if verbose:
        print("  --> %s" % output_path)
    if not dry_run:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # copy input?
        if include_input:
            shutil.copy(path_png, output_png)
            shutil.copy(path_ann, output_ann)

        # label map/wavelengths
        wavelengths = [0]
        reverse_label_map = {"0": "Background"}
        for k in label_map:
            reverse_label_map[str(label_map[k])] = k
            wavelengths.append(label_map[k])
        with open(output_labels, "w") as fp:
            json.dump(reverse_label_map, fp, indent=2)

        # envi mask
        envi.save_image(output_envi, np.array(img), dtype=np.uint8, force=True, interleave='BSQ',
                        metadata={'wavelength': wavelengths})


def generate(input_dirs, output_dir, output_format=OUTPUT_FORMAT_FLAT, labels=None,
             include_input=False, dry_run=False, verbose=False):
    """
    Generates fake RGB images from the HSI images found in the specified directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param output_dir: the (optional) output directory to place the generated PNG images in instead of alongside HSI images
    :type output_dir: str
    :param output_format: how to store the generated ENVI images
    :type output_format: str
    :param labels: the list of labels to transfer from OPEX into ENVI
    :type labels: list
    :param include_input: whether to copy the PNG/JSON files into the output directory as well
    :type include_input: bool
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    """

    if output_format not in OUTPUT_FORMATS:
        raise Exception("Unknown output format: %s" % output_format)

    if isinstance(input_dirs, str):
        input_dirs = [input_dirs]

    if isinstance(labels, str):
        labels = [x.strip() for x in labels.split(",")]

    for input_dir in input_dirs:
        print("Entering: %s" % input_dir)

        for f in os.listdir(input_dir):
            if not f.lower().endswith(".png"):
                continue

            img_path = os.path.join(input_dir, f)
            ann_path = os.path.splitext(img_path)[0] + ".json"
            if not os.path.exists(ann_path):
                if verbose:
                    print("No annotation for: %s" % img_path)
                continue

            convert(img_path, ann_path, output_dir=output_dir, output_format=output_format,
                    labels=labels, include_input=include_input, dry_run=dry_run, verbose=verbose)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="Turns annotations (PNG and OPEX JSON) into Happy ENVI format.",
        prog="happy-opex2happy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the PNG/OPEX files", required=True)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("-f", "--output_format", choices=OUTPUT_FORMATS, default=OUTPUT_FORMAT_FLAT, help="Defines how to store the data in the output directory.", required=True)
    parser.add_argument("-l", "--labels", type=str, help="The comma-separated list of object labels to export ('Background' is automatically added).", required=True)
    parser.add_argument("-I", "--include_input", action="store_true", help="whether to copy the PNG/JSON file across to the output dir", required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit saving the PNG images", required=False)
    parser.add_argument("-v", "--verbose", action="store_true", help="whether to be more verbose with the output", required=False)
    parsed = parser.parse_args(args=args)
    generate(parsed.input_dir, parsed.output_dir,
             output_format=parsed.output_format, labels=parsed.labels,
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
