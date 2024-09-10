#!/usr/bin/python3
import argparse
import json
import logging
import os
import re
import traceback

from wai.logging import add_logging_level, set_logging_level

from happy.base.app import init_app
from happy.data import DataManager, LABEL_WHITEREF
from happy.data.annotations import locate_annotations
from happy.data import export_sub_images
from opex import ObjectPredictions


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


def generate(input_dirs, output_dirs, writers, regexp=None, recursive=False, labels=None,
             black_ref_locator=None, black_ref_method=None,
             white_ref_locator=None, white_ref_method=None, white_ref_annotations=None,
             black_ref_locator_for_white_ref=None, black_ref_method_for_white_ref=None,
             preprocessing=None, dry_run=False, resume_from=None, run_info=None):
    """
    Generates sub-images from ENVI files with OPEX JSON annotations located in the directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param output_dirs: the output dir(s) to place the generated sub-images in
    :type output_dirs: list
    :param writers: the writer command-line(s) to use for outputting the sub-images
    :type writers: list
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
    :param white_ref_annotations: the OPEX JSON file with the annotated white ref if it cannot be determined automatically
    :type white_ref_annotations: str
    :param black_ref_locator_for_white_ref: the black reference locator to use for finding the black ref data to apply to the white reference scan
    :type black_ref_locator_for_white_ref: str
    :param black_ref_method_for_white_ref: the black reference method to use for applying the black ref data to the white reference scan
    :type black_ref_method_for_white_ref: str
    :param preprocessing: the preprocessing pipeline to apply to the scan
    :type preprocessing: str or None
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param resume_from: the directory to resume the processing from (determined dirs preceding this one will get skipped), ignored if None
    :type resume_from: str
    :param run_info: optional path to JSON file for storing run info in
    :type run_info: str or None
    """
    info = {
        "options": {
            "input_dirs": input_dirs,
            "output_dirs": output_dirs,
            "regexp": regexp,
            "recursive": recursive,
            "labels": labels,
            "black_ref_locator": black_ref_locator,
            "black_ref_method": black_ref_method,
            "white_ref_locator": white_ref_locator,
            "white_ref_method": white_ref_method,
            "white_ref_annotations": white_ref_annotations,
            "black_ref_locator_for_white_ref": black_ref_locator_for_white_ref,
            "black_ref_method_for_white_ref": black_ref_method_for_white_ref,
            "resume_from": resume_from,
            "preprocessing": preprocessing,
            "writers": writers,
        }
    }

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
    if (preprocessing is not None) and (len(preprocessing.strip()) == 0):
        preprocessing = None
        
    if (regexp is not None) and (len(regexp) == 0):
        regexp = None
    if (labels is not None) and (len(labels) == 0):
        labels = None

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
                logger.warning("Failed to locate label %s in OPEX JSON file: %s" % (LABEL_WHITEREF, white_ref_annotations))
            else:
                whiteref_ann = (whiteref_obj.bbox.top, whiteref_obj.bbox.left, whiteref_obj.bbox.bottom, whiteref_obj.bbox.right)
        else:
            logger.warning("OPEX JSON file not found (white ref annotations): %s" % white_ref_annotations)

    datamanager = DataManager(log_method=log)
    if black_ref_locator is not None:
        logger.info("Black ref locator: %s" % black_ref_locator)
        datamanager.set_blackref_locator(black_ref_locator)
        logger.info("Black ref method: %s" % black_ref_method)
        datamanager.set_blackref_method(black_ref_method)
    if white_ref_locator is not None:
        logger.info("White ref locator: %s" % white_ref_locator)
        datamanager.set_whiteref_locator(white_ref_locator)
        logger.info("White ref method: %s" % white_ref_method)
        datamanager.set_whiteref_method(white_ref_method)
    if whiteref_ann is not None:
        logger.info("White ref annotations file: %s" % str(white_ref_annotations))
        logger.info("White ref annotations region: %s" % str(whiteref_ann))
    if black_ref_locator_for_white_ref is not None:
        logger.info("Black ref locator used for white ref scans: %s" % black_ref_locator_for_white_ref)
        datamanager.set_blackref_locator_for_whiteref(black_ref_locator_for_white_ref)
        logger.info("Black ref method use for white ref scans: %s" % black_ref_method_for_white_ref)
        datamanager.set_blackref_method_for_whiteref(black_ref_method_for_white_ref)
    if preprocessing is not None:
        logger.info("Preprocessing: %s" % preprocessing)
        datamanager.set_preprocessors(preprocessing)

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

    info["files"] = list()
    for i, ann_cont in enumerate(ann_conts, start=1):
        logger.info("Processing %d/%d..." % (i, len(ann_conts)))
        try:
            logger.info("Base ENVI file: %s" % ann_cont.base)
            datamanager.load_scan(ann_cont.base)
            datamanager.load_contours(ann_cont.opex)
            if whiteref_ann is not None:
                logger.info("Setting white ref annotation: %s" % str(whiteref_ann))
                datamanager.set_whiteref_annotation(whiteref_ann, False)
            datamanager.calc_norm_data()
            if labels is not None:
                matches = datamanager.contours.get_contours_regexp(labels)
                logger.info("Label matches: %d" % len(matches))
                if len(matches) == 0:
                    continue

            info_file = {"file": ann_cont.base}
            if not dry_run:
                for output_dir, writer in zip(output_dirs, writers):
                    msg = export_sub_images(datamanager, output_dir, labels, False, writer_cmdline=writer)
                    if msg is not None:
                        logger.error(msg)
                        if "error" not in info_file:
                            info_file["error"] = dict()
                        info_file["error"][writer] = msg
            info["files"].append(info_file)

        except:
            logger.exception("Failed to process: %s" % ann_cont.base)

    # output run info?
    if (not dry_run) and (run_info is not None):
        logger.info("Writing run info to: %s" % run_info)
        with open(run_info, "w") as fp:
            json.dump(info, fp, indent=2)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    init_app()
    parser = argparse.ArgumentParser(
        description="Exports sub-images from ENVI files annotated with OPEX JSON files. Used for extracting sub-samples. Multiple output/writer pairs can be specified to output in multiple formats in one go.",
        prog="happy-sub-images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", metavar="DIR", type=str, help="Path to the files to generate sub-images from", required=True)
    parser.add_argument("-e", "--regexp", type=str, metavar="REGEXP", help="The regexp for matching the ENVI base files (name only), e.g., for selecting a subset.", required=False, default=None)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to look for files recursively", required=False)
    parser.add_argument("-o", "--output_dir", type=str, metavar="DIR", help="The dir(s) to store the generated sub-images in.", nargs="+")
    parser.add_argument("-w", "--writer", metavar="CMDLINE", help="the writer(s) to use for saving the generated sub-images", default="happy-writer", nargs="+")
    parser.add_argument("-l", "--labels", type=str, help="The regexp for the labels to export.", required=False, default=None)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size", default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual", default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size", default=None, required=False)
    parser.add_argument("--white_ref_annotations", metavar="FILE", help="the OPEX JSON file with the annotated white reference if it cannot be determined automatically", default=None, required=False)
    parser.add_argument("--black_ref_locator_for_white_ref", metavar="LOCATOR", help="the reference locator scheme to use for locating black references that get applied to the white reference, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method_for_white_ref", metavar="METHOD", help="the black reference method to use for applying black references to the white reference, eg br-same-size", default=None, required=False)
    parser.add_argument("--preprocessing", metavar="PIPELINE", help="the preprocessors to apply to the scan", default=None, required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit generating any data or creating directories", required=False)
    parser.add_argument("-R" ,"--resume_from", metavar="DIR", type=str, help="The directory to restart the processing with (all determined dirs preceding this one get skipped)", required=False, default=None)
    parser.add_argument("-I", "--run_info", metavar="FILE", type=str, help="The JSON file to store some run information in.", required=False, default=None)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)
    set_logging_level(logger, parsed.logging_level)
    generate(parsed.input_dir, parsed.output_dir, parsed.writer,
             regexp=parsed.regexp, recursive=parsed.recursive, labels=parsed.labels,
             black_ref_locator=parsed.black_ref_locator, black_ref_method=parsed.black_ref_method,
             white_ref_locator=parsed.white_ref_locator, white_ref_method=parsed.white_ref_method,
             white_ref_annotations=parsed.white_ref_annotations,
             black_ref_locator_for_white_ref=parsed.black_ref_locator_for_white_ref,
             black_ref_method_for_white_ref=parsed.black_ref_method_for_white_ref,
             preprocessing=parsed.preprocessing,
             dry_run=parsed.dry_run, resume_from=parsed.resume_from,
             run_info=parsed.run_info)


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
