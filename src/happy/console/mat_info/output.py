import argparse
import numpy as np
import os
import scipy.io as sio
import sys
import traceback

from happy.data import configure_envi_settings


def main():
    configure_envi_settings()
    parser = argparse.ArgumentParser(
        description='Load and display structs from a MATLAB file.',
        prog="happy-mat-info",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_file', type=str, help='Path to the MATLAB file', required=True)
    parser.add_argument('-o', '--output_file', type=str, help='Path to the output file; outputs to stdout if omitted', default=None)
    args = parser.parse_args()

    mat_file = sio.loadmat(args.input_file)
    struct_names = [name for name in mat_file.keys() if isinstance(mat_file[name], np.ndarray)]

    if (args.output_file is None) or os.path.isdir(args.output_file):
        output = sys.stdout
    else:
        output = open(args.output_file, "w")

    if not struct_names:
        output.write("No structs found in the MATLAB file.\n")
    else:
        output.write("Available structs:\n\n")
        for name in struct_names:
            output.write(f"Struct: {name}\n")
            output.write(f"Data type: {mat_file[name].dtype}\n")
            output.write(f"Shape: {mat_file[name].shape}\n")

            if np.issubdtype(mat_file[name].dtype, np.integer):
                unique_values = np.unique(mat_file[name])
                output.write("Unique integer values: ")
                output.write(str(unique_values))
                output.write("\n")
            output.write("\n")

    if output != sys.stdout:
        output.close()


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
