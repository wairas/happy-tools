import argparse
import logging
import traceback

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.data.annotations import locate_opex
from opex import ObjectPredictions


PROG = "happy-opex-labels"


ACTION_LIST_LABELS = "list-labels"
ACTIONS = [
    ACTION_LIST_LABELS,
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


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Performs actions on OPEX JSON files that it locates.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=str, help='The dir(s) with the OPEX JSON files', required=True, nargs="+")
    parser.add_argument('-r', '--recursive', action="store_true", help='Whether to search the directory recursively', default=False, required=False)
    parser.add_argument('-a', '--action', choices=ACTIONS, default=ACTION_LIST_LABELS, help='The action to perform', required=False)
    parser.add_argument('-o', '--output_file', type=str, help='Path to the output file; outputs to stdout if omitted', default=None)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args()
    set_logging_level(logger, parsed.logging_level)

    # locate files
    opex_files = []
    locate_opex(parsed.input, opex_files, recursive=parsed.recursive, require_png=False, logger=logger)

    # perform action
    if parsed.action == ACTION_LIST_LABELS:
        list_labels(opex_files, parsed.output_file)
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
