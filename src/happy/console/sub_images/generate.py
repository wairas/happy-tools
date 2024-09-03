#!/usr/bin/python3
import argparse
import logging
import os
import re
import traceback

from wai.logging import add_logging_level, set_logging_level

from happy.base.app import init_app
from happy.data import DataManager
from happy.data.annotations import locate_annotations
from happy.data import export_sub_images


logger = logging.getLogger("sub-images")


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


def generate(input_dirs, output_dir, regexp=None, recursive=False, labels=None,
             black_ref_locator=None, black_ref_method=None,
             white_ref_locator=None, white_ref_method=None,
             dry_run=False, resume_from=None, writer="happy-writer"):
    """
    Generates sub-images from ENVI files with OPEX JSON annotations located in the directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param output_dir: the output directory to place the generated sub-images in
    :type output_dir: str
    :param regexp: the regular expression to match against the ENVI base name, e.g., for processing subset
    :type regexp: str or None
    :param recursive: whether to look for files recursively
    :type recursive: bool
    :param labels: the regexp for labels to export
    :type labels: str or None
    :param black_ref_locator: reference locator for black reference files, ignored if None
    :type black_ref_locator: str
    :param black_ref_method: the black reference method to apply, ignored if None
    :type black_ref_method: str
    :param white_ref_locator: reference locator for white reference files, ignored if None
    :type white_ref_locator: str
    :param white_ref_method: the white reference method to apply, ignored if None
    :type white_ref_method: str
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param resume_from: the directory to resume the processing from (determined dirs preceding this one will get skipped), ignored if None
    :type resume_from: str
    :param writer: the writer command-line to use for outputting the sub-images
    :type writer: str
    """
    if black_ref_locator is None:
        black_ref_method = None
    if black_ref_method is None:
        black_ref_locator = None
    if white_ref_locator is None:
        white_ref_method = None
    if white_ref_method is None:
        white_ref_locator = None
        
    if (regexp is not None) and (len(regexp) == 0):
        regexp = None
    if (labels is not None) and (len(labels) == 0):
        labels = None
        
    datamanager = DataManager(log_method=log)
    datamanager.set_blackref_locator(black_ref_locator)
    datamanager.set_blackref_method(black_ref_method)
    datamanager.set_whiteref_locator(white_ref_locator)
    datamanager.set_whiteref_method(white_ref_method)

    ann_conts = []
    locate_annotations(input_dirs, ann_conts, recursive=recursive,
                       require_envi_mask=False, require_png=False, require_opex=True, logger=logger)
    ann_conts = sorted(ann_conts)
    logger.info("# files located: %d" % len(ann_conts))

    # subset?
    if regexp is not None:
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
        for ann_cont in ann_conts:
            ann_dir = os.path.dirname(ann_cont)
            if ann_dir.startswith(resume_from):
                found = True
            if found:
                _ann_conts.append(ann_cont)
        if len(_ann_conts) == 0:
            raise Exception("Resuming from dir '%s' resulted in an empty set of annotations to process!" % resume_from)
        else:
            logger.info("Resume from dir '%s' changed number of annotations to process from %d to %d." % (resume_from, len(ann_conts), len(_ann_conts)))
        ann_conts = _ann_conts
        logger.info("# files to resume from %s: %d" % (resume_from, len(ann_conts)))

    for i, ann_cont in enumerate(ann_conts, start=1):
        logger.info("Processing %d/%d..." % (i, len(ann_conts)))
        try:
            logger.info("Base ENVI file: %s" % ann_cont.base)
            datamanager.load_scan(ann_cont.base)
            datamanager.load_contours(ann_cont.opex)
            datamanager.calc_norm_data()
            if labels is not None:
                matches = datamanager.contours.get_contours_regexp(labels)
                logger.info("Label matches: %d" % len(matches))
                if len(matches) == 0:
                    continue

            if not dry_run:
                msg = export_sub_images(datamanager, output_dir, labels, False, writer_cmdline=writer)
                if msg is not None:
                    logger.error(msg)

        except:
            logger.exception("Failed to process: %s" % ann_cont.base)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    init_app()
    parser = argparse.ArgumentParser(
        description="Exports sub-images from ENVI files annotated with OPEX JSON files. Used for extracting sub-samples.",
        prog="happy-sub-images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the files to generate sub-images from", required=True)
    parser.add_argument("--regexp", type=str, metavar="REGEXP", help="The regexp for matching the ENVI base files (name only), e.g., for selecting a subset.", required=False, default=None)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to look for files recursively", required=False)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The directory to store the generated sub-images in.", required=False)
    parser.add_argument("-l", "--labels", type=str, help="The regexp for the labels to export.", required=False, default=None)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size", default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual", default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size", default=None, required=False)
    parser.add_argument("--writer", metavar="CMDLINE", help="the writer to use for saving the generated sub-images", default="happy-writer", required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit generating any data or creating directories", required=False)
    parser.add_argument("--resume_from", metavar="DIR", type=str, help="The directory to restart the processing with (all determined dirs preceding this one get skipped)", required=False, default=None)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)
    set_logging_level(logger, parsed.logging_level)
    generate(parsed.input_dir, parsed.output_dir, regexp=parsed.regexp, recursive=parsed.recursive, labels=parsed.labels,
             black_ref_locator=parsed.black_ref_locator, black_ref_method=parsed.black_ref_method,
             white_ref_locator=parsed.white_ref_locator, white_ref_method=parsed.white_ref_method,
             dry_run=parsed.dry_run, resume_from=parsed.resume_from, writer=parsed.writer)


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
