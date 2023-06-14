import json
import os


def simple_filename_func(base_dir, sample_id):
    base_id, sub_dir, _ = sample_id.split("__")
    return os.path.join(base_dir, sub_dir, "normcubes", f"{base_id}.mat")


def get_objectid_from_sampleid(sample_id):
    _, _, objid = sample_id.split("__")
    return int(objid)


def load_sampleids(filename):
    """
    Loads the JSON array with the sample IDs to process.

    :param filename: the JSON file to load (must contain an array)
    :type filename: str
    :return: the list
    :rtype: list
    """
    with open(filename) as f:
        data = json.load(f)
    return data