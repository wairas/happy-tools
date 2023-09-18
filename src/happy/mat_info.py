import argparse
import numpy as np
import scipy.io as sio
import traceback


def main():
    parser = argparse.ArgumentParser(
        description='Load and display structs from a MATLAB file.',
        prog="happy-mat-info",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('matfile', type=str, help='Path to the MATLAB file')
    args = parser.parse_args()

    mat_file = sio.loadmat(args.matfile)
    struct_names = [name for name in mat_file.keys() if isinstance(mat_file[name], np.ndarray)]

    if not struct_names:
        print("No structs found in the MATLAB file.")
    else:
        print("Available structs:")
        for name in struct_names:
            print(f"Struct: {name}")
            print(f"Data type: {mat_file[name].dtype}")
            print(f"Shape: {mat_file[name].shape}")

            if np.issubdtype(mat_file[name].dtype, np.integer):
                unique_values = np.unique(mat_file[name])
                print("Unique integer values:")
                print(unique_values)
            print()


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
