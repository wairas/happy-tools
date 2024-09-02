import argparse
import csv
import io
import json
import logging
import os
import sys
import traceback

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data.annotations import MASK_PREFIX
from opex import ObjectPredictions
from PIL import Image
from tabulate import tabulate


PROG = "happy-raw-check"

RESULT_FIELD_DIR = "dir"
RESULT_FIELD_SAMPLE_ID = "sample_id"
RESULT_FIELD_SCAN = "scan"
RESULT_FIELD_POLYGON_ANNOTATIONS = "polygon-annotations"
RESULT_FIELD_PIXEL_ANNOTATIONS = "pixel-annotations"
RESULT_FIELD_SCREENSHOT = "screenshot"
RESULT_FIELD_DARKREF = "darkref"
RESULT_FIELD_POLYGON_LABELS = "polygon-labels"
RESULT_FIELD_PIXEL_LABELS = "pixel-labels"
RESULT_FIELDS = [
    RESULT_FIELD_DIR,
    RESULT_FIELD_SAMPLE_ID,
    RESULT_FIELD_SCAN,
    RESULT_FIELD_POLYGON_ANNOTATIONS,
    RESULT_FIELD_PIXEL_ANNOTATIONS,
    RESULT_FIELD_SCREENSHOT,
    RESULT_FIELD_DARKREF,
    RESULT_FIELD_POLYGON_LABELS,
    RESULT_FIELD_PIXEL_LABELS,
]


OUTPUT_FORMAT_TEXT = "text"
OUTPUT_FORMAT_TEXT_COMPACT = "text-compact"
OUTPUT_FORMAT_CSV = "csv"
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMATS = [
    OUTPUT_FORMAT_TEXT,
    OUTPUT_FORMAT_TEXT_COMPACT,
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMAT_JSON,
]


logger = logging.getLogger(PROG)


def locate_capture_dirs(input_dirs, capture_dirs, recursive=False):
    """
    Locates the PNG/OPEX JSON pairs.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param capture_dirs: for collecting the OPEX JSON files
    :type capture_dirs: list
    :param recursive: whether to look for OPEX files recursively
    :type recursive: bool
    """
    if isinstance(input_dirs, str):
        input_dirs = [input_dirs]

    for input_dir in input_dirs:
        if logger is not None:
            logger.info("Entering: %s" % input_dir)

        for f in os.listdir(input_dir):
            full = os.path.join(input_dir, f)

            # directory?
            if os.path.isdir(full):
                if f == "capture":
                    capture_dirs.append(full)
                elif recursive:
                    locate_capture_dirs(full, capture_dirs, recursive=recursive)
                    if logger is not None:
                        logger.info("Back in: %s" % input_dir)


def get_sample_id(path):
    """
    Returns the sample ID from the directory (ie the capture dir's parent).

    :param path: the capture dir to get the sample ID from
    :type path: str
    :return: the sample ID, None if failed
    :rtype: str
    """
    if os.path.dirname(path) is not None:
        return os.path.basename(os.path.dirname(path))
    return None


def check_dir(path):
    """
    Checks the directory and returns the result.

    :param path: the capture dir to check
    :type path: str
    :return: the result
    :rtype: dict
    """
    result = {
        RESULT_FIELD_DIR: path,
        RESULT_FIELD_SAMPLE_ID: False,
        RESULT_FIELD_SCAN: False,
        RESULT_FIELD_POLYGON_ANNOTATIONS: False,
        RESULT_FIELD_PIXEL_ANNOTATIONS: False,
        RESULT_FIELD_SCREENSHOT: False,
        RESULT_FIELD_DARKREF: False,
        RESULT_FIELD_POLYGON_LABELS: list(),
        RESULT_FIELD_PIXEL_LABELS: list(),
    }

    # sample ID
    sample_id = get_sample_id(path)
    if sample_id is not None:
        result[RESULT_FIELD_SAMPLE_ID] = True

        # scan
        f = os.path.join(path, sample_id + ".hdr")
        if os.path.exists(f):
            result[RESULT_FIELD_SCAN] = True

        # polygon annotations
        f = os.path.join(path, sample_id + ".json")
        if os.path.exists(f):
            try:
                preds = ObjectPredictions.load_json_from_file(f)
                result[RESULT_FIELD_POLYGON_ANNOTATIONS] = True
                labels = set()
                for obj in preds.objects:
                    if " " in obj.label:
                        labels.add("'%s'" % obj.label)
                    else:
                        labels.add(obj.label)
                result[RESULT_FIELD_POLYGON_LABELS] = sorted(list(labels))
            except:
                pass

        # pixel annotations
        f = os.path.join(path, MASK_PREFIX + sample_id + ".hdr")
        if os.path.exists(f):
            result[RESULT_FIELD_PIXEL_ANNOTATIONS] = True
            f = os.path.join(path, MASK_PREFIX + sample_id + ".json")
            if os.path.exists(f):
                try:
                    with open(f, "r") as fp:
                        label_map = json.load(fp)
                    result[RESULT_FIELD_PIXEL_LABELS] = sorted(label_map.values())
                except:
                    pass

        # screenshot
        f = os.path.join(path, sample_id + ".png")
        if os.path.exists(f):
            try:
                Image.open(f)
                result[RESULT_FIELD_SCREENSHOT] = True
            except:
                pass

        # darkref
        f = os.path.join(path, "DARKREF_" + sample_id + ".hdr")
        if os.path.exists(f):
            result[RESULT_FIELD_DARKREF] = True

    return result


def output_results(results, output=None, output_format=OUTPUT_FORMAT_TEXT, return_results=False, use_stdout=True):
    """
    Outputs the results of the check. If no output file is given, stdout is used.

    :param results: the list of result dictionaries to output
    :type results: list
    :param output: the file to output the results to, uses stdout if None
    :type output: str
    :param output_format: the type of format to generate
    :type output_format: str
    :param return_results: whether to return the results
    :type return_results: bool
    :param use_stdout: whether to output on stdout if no output file given
    :param use_stdout: bool
    :return: the results, None if return_results is False
    :rtype: str
    """
    result = None

    if output_format not in OUTPUT_FORMATS:
        raise Exception("Invalid output format: %s" % output_format)

    rows = None
    if output_format in [OUTPUT_FORMAT_TEXT, OUTPUT_FORMAT_CSV]:
        rows = list()
        rows.append([x for x in RESULT_FIELDS])
        for result in results:
            row = []
            for field in RESULT_FIELDS:
                if field == RESULT_FIELD_POLYGON_LABELS:
                    row.append("|".join(result[field]))
                elif field == RESULT_FIELD_PIXEL_LABELS:
                    row.append("|".join(result[field]))
                else:
                    row.append(result[field])
            rows.append(row)

    if output_format == OUTPUT_FORMAT_TEXT:
        table = tabulate(rows, headers='firstrow', tablefmt='fancy_grid')
        if output is None:
            if use_stdout:
                print(table)
        else:
            with open(output, "w") as fp:
                fp.write(table)
                fp.write("\n")
        if return_results:
            result = table

    elif output_format == OUTPUT_FORMAT_TEXT_COMPACT:
        lines = list()
        for result in results:
            lines.append(result[RESULT_FIELD_DIR])
            for field in RESULT_FIELDS:
                if field != RESULT_FIELD_DIR:
                    if field == RESULT_FIELD_POLYGON_LABELS:
                        value = "|".join(result[field])
                    else:
                        value = str(result[field])
                    lines.append("   " + field + ": " + value)
            lines.append("")
        full = "\n".join(lines)
        if output is None:
            if use_stdout:
                print(full)
        else:
            with open(output, "w") as fp:
                fp.write(full)
        if return_results:
            result = full

    elif output_format == OUTPUT_FORMAT_CSV:
        writer = None
        fp = None
        if output is None:
            if use_stdout:
                writer = csv.writer(sys.stdout)
                fp = None
        else:
            fp = open(output, "w")
            writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
        if writer is not None:
            writer.writerows(rows)
        if fp is not None:
            fp.close()
        if return_results:
            buf = io.StringIO()
            buf.write("\ufeff")
            writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows)
            result = buf.getvalue()

    elif output_format == OUTPUT_FORMAT_JSON:
        if output is None:
            if use_stdout:
                print(json.dumps(results, indent=2))
        else:
            with open(output, "w") as fp:
                json.dump(results, fp, indent=2)
        if return_results:
            result = json.dumps(results, indent=2)

    else:
        raise Exception("Unsupported output format: %s" % output_format)

    return result


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Performs sanity checks on raw capture folders.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=str, help='The dir(s) with the raw capture folders', required=True, nargs="+")
    parser.add_argument('-r', '--recursive', action="store_true", help='Whether to search the directory recursively', default=False, required=False)
    parser.add_argument('-o', '--output', type=str, help='The file to store the results in; uses stdout if omitted', required=False, default=None)
    parser.add_argument('-f', '--output_format', choices=OUTPUT_FORMATS, help='The format to use for the output', required=False, default=OUTPUT_FORMAT_TEXT)
    add_logging_level(parser, short_opt="-V")

    parsed = parser.parse_args()
    set_logging_level(logger, parsed.logging_level)

    # check "capture" dirs
    capture_dirs = []
    locate_capture_dirs(parsed.input, capture_dirs, recursive=parsed.recursive)
    capture_dirs = sorted(capture_dirs)
    results = []
    for capture_dir in capture_dirs:
        results.append(check_dir(capture_dir))

    # output results
    output_results(results, output=parsed.output, output_format=parsed.output_format)


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
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
