import logging
import os

from dataclasses import dataclass
from typing import List

from ._pixels import MASK_PREFIX


@dataclass
class AnnotationFiles:
    """
    Container for files representing annotations.
    """
    base: str = None
    opex: str = None
    png: str = None
    envi_mask: str = None

    def _is_less(self, this, other):
        if (this is None) and (other is None):
            return False
        if this is None:
            return True
        if other is None:
            return False
        return this < other

    def _is_equal(self, this, other):
        if (this is None) and (other is None):
            return True
        if this is None:
            return False
        if other is None:
            return False
        return this == other

    def __lt__(self, other):
        return self._is_less(self.base, other.base)

    def __eq__(self, other):
        return self._is_equal(self.base, other.base)


def locate_annotations(input_dirs, ann_files: List[AnnotationFiles], recursive=False, require_opex=False,
                       require_png=False, require_envi_mask=False, require_opex_or_envi=False, logger=None):
    """
    Locates the PNG/OPEX JSON/ENVI pixel mask files.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param ann_files: for collecting the annotation files
    :type ann_files: list
    :param recursive: whether to look for annotation files recursively
    :type recursive: bool
    :param require_opex: whether a OPEX JSON file must be present
    :type require_opex: bool
    :param require_png: whether a PNG file must be present
    :type require_png: bool
    :param require_envi_mask: whether an ENVI mask file must be present
    :type require_envi_mask: bool
    :param require_opex_or_envi: either OPEX JSON or ENVI mask file must be present (both can be present)
    :type require_opex_or_envi: bool
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
                    locate_annotations(full, ann_files, recursive=recursive,
                                       require_opex=require_opex, require_png=require_png,
                                       require_envi_mask=require_envi_mask, require_opex_or_envi=require_opex_or_envi,
                                       logger=logger)
                    if logger is not None:
                        logger.info("Back in: %s" % input_dir)
                else:
                    continue

            if not f.endswith(".hdr"):
                continue
            if f.startswith(MASK_PREFIX):
                continue

            full_path = os.path.join(input_dir, f)
            prefix = os.path.splitext(full_path)[0]

            # opex json
            opex_path = prefix + ".json"
            if not os.path.exists(opex_path):
                opex_path = None

            # png
            png_path = prefix + ".png"
            if not os.path.exists(png_path):
                png_path = None

            # envi mask
            envi_mask_path = os.path.join(os.path.dirname(prefix), MASK_PREFIX + os.path.basename(prefix) + ".hdr")
            if not os.path.exists(envi_mask_path):
                envi_mask_path = None

            # no annotations at all
            if (opex_path is None) and (png_path is None) and (envi_mask_path is None):
                continue
            # no opex?
            if require_opex and (opex_path is None):
                if logger is not None:
                    logger.info("No annotation OPEX JSON file for: %s" % (prefix + ".*"))
                continue
            # no png?
            if require_png and (png_path is None):
                if logger is not None:
                    logger.info("No annotation PNG file for: %s" % (prefix + ".*"))
                continue
            # no envi mask?
            if require_envi_mask and (envi_mask_path is None):
                if logger is not None:
                    logger.info("No annotation ENVI mask file for: %s" % (prefix + ".*"))
                continue
            # either opex or envi mask?
            if require_opex_or_envi and (opex_path is None) and (envi_mask_path is None):
                if logger is not None:
                    logger.info("Neither OPEX JSON nor ENVI mask file for: %s" % (prefix + ".*"))
                continue

            ann_files.append(AnnotationFiles(base=full_path, opex=opex_path, png=png_path, envi_mask=envi_mask_path))
