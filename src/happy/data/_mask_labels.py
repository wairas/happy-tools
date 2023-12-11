import os
import json

from typing import Dict, List


DEFAULT_MASK_LABELS_FILE = "mask.json"
""" the default name for the mask labels. """


def load_mask_labels(path: str, fail_on_error: bool = False) -> Dict[str, str]:
    """
    For loading a mask.json file
    :param path:
    :param fail_on_error:
    :return:
    """
    result = {}
    if os.path.exists(path):
        with open(path, "r") as fp:
            result = json.load(fp)
        if not isinstance(result, dict):
            if fail_on_error:
                raise Exception("Expected to load dictionary from '%s' but got: %s" % (path, str(type(result))))
            else:
                result = {}
    else:
        if fail_on_error:
            raise Exception("Mask labels file missing: %s" % path)

    return result


def get_label_indices(labels: Dict[str, str]) -> List[int]:
    """
    Turns the string integer keys of the labels dictionary into a list of integer indices.

    :param labels: the labels dictionary to process
    :type labels: dict
    :return: the list of int indices
    :rtype: list
    """
    result = []
    for k in labels:
        try:
            result.append(int(k))
        except:
            pass
    return result


def locate_mask_files(base_folder: str, mask_file: str = "mask.json") -> List[str]:
    """
    Lists all the mask files in the base-folder and its sub-folders.

    :param base_folder: the base folder to start the search in
    :type base_folder: str
    :param mask_file: the mask file to look for
    :type mask_file: str
    :return: the mask files
    :rtype: list
    """
    result = []

    for f in os.listdir(base_folder):
        full = os.path.join(base_folder, f)
        if os.path.isdir(full):
            result.extend(locate_mask_files(full, mask_file=mask_file))
        elif f == mask_file:
            result.append(full)

    return result


def determine_label_indices(base_folder: str, mask_file: str = "mask.json") -> List[int]:
    """
    Determines the indices of the classes defined in the mask_file files.

    :param base_folder: the base folder to start the search in
    :type base_folder: str
    :param mask_file: the mask file to look for
    :type mask_file: str
    :return: the indices, -1 if failed to determine
    :rtype: list
    """
    result = []

    mask_files = locate_mask_files(base_folder, mask_file=mask_file)
    for f in mask_files:
        labels = load_mask_labels(f, fail_on_error=False)
        indices = get_label_indices(labels)
        for index in indices:
            if index not in result:
                result.append(index)

    result = sorted(result)
    return result


def check_labels(base_folder: str, mask_file: str = "mask.json") -> int:
    """
    Ensures that the labels are all the same.

    :param base_folder: the base folder to start the search in
    :type base_folder: str
    :param mask_file: the mask file to look for
    :type mask_file: str
    :return: True if the same
    :rtype: bool
    """
    result = True

    mask_files = locate_mask_files(base_folder, mask_file=mask_file)
    labels_cur = None
    for f in mask_files:
        labels_old = labels_cur
        labels_cur = load_mask_labels(f, fail_on_error=False)
        if labels_old is not None:
            if labels_old != labels_cur:
                result = False
                break

    return result
