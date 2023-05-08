import argparse
import json
import os
import traceback
from datetime import datetime

import numpy as np
import pandas as pd

from criteria import Criteria
from pixel_selectors.averaged_grid_pixel_selector import AveragedGridSelector
from pixel_selectors.column_wise_pixel_selector import ColumnWisePixelSelector
from readers.mat_reader import MatReader


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


def simple_filename_func(base_dir, sample_id):
    base_id, sub_dir, _ = sample_id.split("__")
    return os.path.join(base_dir, sub_dir, "normcubes", f"{base_id}.mat")


def load_global_jsons(ids_filename, output_path, spectra_reader, pixel_selectors, meta_data_keys, target_keys):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    output_dict = {}
    ids = load_sampleids(ids_filename)
    for pixel_selector in pixel_selectors:
        print("Generating data for: %s" % pixel_selector.__class__.__name__)

        # Create the filename for the CSV and JSON files
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        columns_created = False
        output_df = pd.DataFrame()
        for id in ids:
            # if filename.endswith("_global.json"):
            # Load the global json
            # print(filename)
            # id = filename[:-len("_global.json")]
            print(id)
            spectra_reader.load_data(id)

            selectedp = pixel_selector.select_pixels()

            wn = spectra_reader.get_wavelengths()
            for ind, (x, y, z_data) in enumerate(selectedp):
                # If pixel type is valid and z data is not zero, add row to output dataframe
                if not np.all(z_data == 0):
                    if not columns_created:
                        column_names = meta_data_keys + [f"z_{wn[i]}" for i in range(len(z_data))] + target_keys
                        output_df = pd.DataFrame(columns=column_names)
                        columns_created = True
                    # Create a dictionary of values for the row
                    row_values = {
                        key: spectra_reader.json_reader.get_meta_data(x=x, y=y, key=key)
                        for key in meta_data_keys
                    }
                    row_values.update({f"z_{wn[i]}": v for i, v in enumerate(z_data)})
                    row_values.update({
                        key: spectra_reader.json_reader.get_meta_data(x=x, y=y, key=key)
                        for key in target_keys
                    })

                    # Add the row to the output dataframe
                    output_df = output_df.append(row_values, ignore_index=True)

        # Write the multi-target output CSV file
        n = pixel_selector.get_n()
        target = "multi_target"
        filename = f"{pixel_selector.__class__.__name__}_{n}_{timestamp}.csv"
        output_dir = os.path.join(output_path, target)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, filename)
        if target not in output_dict:
            output_dict[target] = {}
        output_dict[target][filename] = pixel_selector.to_dict()
        output_df.to_csv(output_file, index=False, columns=column_names)
        # output_file = os.path.join(output_path, filename)
        # output_dict[filename] = pixel_selector.to_dict()
        # output_df.to_csv(output_file, index=False, columns=column_names)

        for target in target_keys:
            # make columns
            column_names = meta_data_keys + [f"z_{wn[i]}" for i in range(len(z_data))] + [target]
            # output dir/file
            output_dir = os.path.join(output_path, target)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_file = os.path.join(output_dir, filename)
            if target not in output_dict:
                output_dict[target] = {}
            output_dict[target][filename] = pixel_selector.to_dict()
            output_df.to_csv(output_file, index=False, columns=column_names)
            # Add the pixel selector dictionary to the output dictionary

    # Write the output JSON file
    output_json = os.path.join(output_path, "output_csvs.json")
    with open(output_json, "w") as f:
        json.dump(output_dict, f, indent=2)


def generate(data_dir, metadata_dir, sample_ids, output_dir, metadata_values, targets):
    """
    Generates the CSV output.

    :param data_dir: the directory with the data hyper-spectral data files to process
    :type data_dir: str
    :param metadata_dir: the directory with the JSON meta-data files
    :type metadata_dir: str
    :param sample_ids: the JSON file with the array of sample IDs to process
    :type sample_ids: str
    :param output_dir: the directory to store the output in
    :type output_dir: str
    :param metadata_values: the names of the meta-data values to add to the output
    :type metadata_values: list
    :param targets: the list of names of targets to generate data for
    :type targets: list
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Folder '{output_dir}' created successfully!")
    else:
        print(f"Folder '{output_dir}' already exists.")

    # Initialize the spectra reader object for reading .mat files
    mat_reader = MatReader(data_dir,
                           metadata_dir, simple_filename_func, "normcube",
                           wavelengths_struct="lambda")

    crit = Criteria("in", key="type", value=[2, 3], spectra_reader=mat_reader)
    pixel_selectors = [AveragedGridSelector(mat_reader, 32, crit, 4), AveragedGridSelector(mat_reader, 4, crit, 4),
                       AveragedGridSelector(mat_reader, 4, crit, 2), ColumnWisePixelSelector(mat_reader, 32, crit, 4)]

    # process files
    load_global_jsons(sample_ids, output_dir, mat_reader, pixel_selectors,
                      metadata_values, targets)


def main(args=None):
    """
    The main method for parsing command-line arguments and labeling.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="Generates CSV files from hyper-spectral images.",
        prog="h2c-generate-csv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--data_dir", metavar="DIR", help="the directory with the hyper-spectral data files", required=True)
    parser.add_argument("-m", "--metadata_dir", metavar="DIR", help="the directory with the meta-data JSON files", required=True)
    parser.add_argument("-s", "--sample_ids", metavar="FILE", help="the JSON file with the array of sample IDs to process", required=True)
    parser.add_argument("-o", "--output_dir", metavar="DIR", help="the directory to store the results in", required=True)
    parser.add_argument("-M", "--metadata_values", nargs="*", help="the meta-data values to add to the output", required=False)
    parser.add_argument("-T", "--targets", nargs="+", help="the target values to generate data for", required=True)
    parsed = parser.parse_args(args=args)
    generate(parsed.data_dir, parsed.metadata_dir, parsed.sample_ids, parsed.output_dir,
             parsed.metadata_values, parsed.targets)


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
