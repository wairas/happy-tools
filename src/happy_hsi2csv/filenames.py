import os


# TODO turn into command-line option
def simple_filename_func(base_dir, sample_id):
    base_id, sub_dir, _ = sample_id.split("__")
    return os.path.join(base_dir, sub_dir, "normcubes", f"{base_id}.mat")