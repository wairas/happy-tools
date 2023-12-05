import argparse
import logging
import traceback

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data.annotations import locate_opex
from opex import ObjectPredictions


PROG = "happy-opex-labels"


LABEL_MAPPING_FORMAT = "old_label<TAB>new_label"


ACTION_LIST_LABELS = "list-labels"
ACTION_UPDATE_LABELS = "update-labels"
ACTIONS = [
    ACTION_LIST_LABELS,
    ACTION_UPDATE_LABELS,
]


logger = logging.getLogger(PROG)


def list_labels(opex_files, output_file):
    """
    Lists the labels obtained from the opex files.

    :param opex_files: the OPEX files to analyze
    :type opex_files: list
    :param output_file: the file to store the list of labels in, uses stdout if None
    :type output_file: str
    """
    labels = set()
    for opex_file in opex_files:
        try:
            logger.info("Processing: %s" % opex_file)
            preds = ObjectPredictions.load_json_from_file(opex_file)
            for obj in preds.objects:
                labels.add(obj.label)
        except:
            logger.exception("Failed to load: %s" % opex_file)

    labels = sorted(list(labels))
    if output_file is not None:
        logger.info("Saving labels in: %s" % output_file)
        with open(output_file, "w") as fp:
            fp.write("\n".join(labels))
    else:
        print("\n".join(labels))


def update_labels(opex_files, mapping, dry_run, output_file):
    """
    Updates the labels stored in the opex files using the specified label mapping (old -> new).

    :param opex_files: the OPEX files to update
    :type opex_files: list
    :param mapping: the label mapping (old -> new)
    :type mapping: dict
    :param dry_run: whether to perform a dry-run, ie not save affected files
    :type dry_run: bool
    :param output_file: the file to store the affected files in , uses stdout if None
    :type output_file: str
    """
    affected_files = []
    for opex_file in opex_files:
        is_affected = False
        preds = None
        try:
            logger.info("Processing: %s" % opex_file)
            preds = ObjectPredictions.load_json_from_file(opex_file)
            for obj in preds.objects:
                if obj.label in mapping:
                    is_affected = True
                    obj.label = mapping[obj.label]
        except:
            logger.exception("Failed to load: %s" % opex_file)
        if is_affected:
            affected_files.append(opex_file)
            if not dry_run and (preds is not None):
                preds.save_json_to_file(opex_file)

    if not dry_run and (output_file is not None):
        logger.info("Saving affected files to: %s" % output_file)
        with open(output_file, "w") as fp:
            fp.write("\n".join(affected_files))
    else:
        print("\n".join(affected_files))


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Performs actions on OPEX JSON files that it locates.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=str, help='The dir(s) with the OPEX JSON files', required=True, nargs="+")
    parser.add_argument('-r', '--recursive', action="store_true", help='Whether to search the directory recursively', default=False, required=False)
    add_logging_level(parser, short_opt="-V")
    subparsers = parser.add_subparsers(help='sub-command help', dest="command")

    # action: list-labels
    parser_list = subparsers.add_parser(ACTION_LIST_LABELS, help='Lists the labels in the located files')
    parser_list.add_argument('-o', '--output_file', type=str, help='Path to the output file for storing the labels; outputs to stdout if omitted', default=None)

    # action: update-labels
    parser_update = subparsers.add_parser(ACTION_UPDATE_LABELS, help='Updates the labels using the specified label mapping')
    parser_update.add_argument('-m', '--label_mapping', type=str, help='Path to the label mapping file when updating labels; format: ' + LABEL_MAPPING_FORMAT, default=None, required=False)
    parser_update.add_argument('-n', '--dry_run', action="store_true", help='Whether to skip saving affected files', default=False, required=False)
    parser_update.add_argument('-o', '--output_file', type=str, help='Path to the output file for storing the affected files; outputs to stdout if omitted', default=None)

    parsed = parser.parse_args()
    set_logging_level(logger, parsed.logging_level)

    # locate files
    opex_files = []
    locate_opex(parsed.input, opex_files, recursive=parsed.recursive, require_png=False, logger=logger)

    # perform action
    if parsed.command == ACTION_LIST_LABELS:
        list_labels(opex_files, parsed.output_file)
    elif parsed.command == ACTION_UPDATE_LABELS:
        if parsed.label_mapping is None:
            raise Exception("No label mapping file provided!")
        mapping = dict()
        with open(parsed.label_mapping, "r") as fp:
            for line in fp.readlines():
                line = line.strip()
                if "\t" in line:
                    parts = line.split("\t")
                    if len(parts) == 2:
                        if parts[0] == parts[1]:
                            logger.info("Skipping identical old/new labels: %s == %s" % (parts[0], parts[1]))
                        else:
                            mapping[parts[0]] = parts[1]
                    else:
                        logger.warning("Expected format '%s' but got: %s" % (LABEL_MAPPING_FORMAT, line))
        if len(mapping) == 0:
            logger.warning("Label mapping is empty, skipping update.")
        else:
            update_labels(opex_files, mapping, parsed.dry_run, parsed.output_file)
    else:
        raise Exception("Unsupported action: %s" % parsed.action)


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
