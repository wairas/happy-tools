import logging
import os


def locate_opex(input_dirs, opex_files, recursive=False, require_png=False, logger=None):
    """
    Locates the PNG/OPEX JSON pairs.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param opex_files: for collecting the OPEX JSON files
    :type opex_files: list
    :param recursive: whether to look for OPEX files recursively
    :type recursive: bool
    :param require_png: whether a PNG file must be present as well
    :type require_png: bool
    :param logger: the optional logger instance to use for outputting logging information
    :type logger: logging.Logger
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
                if recursive:
                    locate_opex(full, recursive, opex_files)
                    if logger is not None:
                        logger.info("Back in: %s" % input_dir)
                else:
                    continue

            if not f.lower().endswith(".json"):
                continue

            ann_path = os.path.join(input_dir, f)
            prefix = os.path.splitext(ann_path)[0]
            img_path = prefix + ".png"
            if require_png and not os.path.exists(img_path):
                if logger is not None:
                    logger.info("No annotation JSON/PNG pair for: %s" % (prefix + ".*"))
                continue
            opex_files.append(ann_path)
