import argparse
import os
import spectral.io.envi as envi
import sys
import traceback

from happy.data import configure_envi_settings


PROG = "happy-hdr-info"


def main():
    configure_envi_settings()
    parser = argparse.ArgumentParser(
        description='Load and print information about an HDR file.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_file', type=str, help='Path to the HDR file', required=True)
    parser.add_argument('-f', '--full', action="store_true", help='Whether to output all fields', required=False)
    parser.add_argument('-o', '--output_file', type=str, help='Path to output file; prints to stdout if omitted', default=None)
    args = parser.parse_args()

    header = envi.read_envi_header(args.input_file)

    if (args.output_file is None) or os.path.isdir(args.output_file):
        output = sys.stdout
    else:
        output = open(args.output_file, "w")

    output.write("Header Information:\n")
    output.write(f"Dimensions: {header['lines']} x {header['samples']}\n")
    output.write(f"Number of Bands: {header['bands']}\n")
    output.write(f"Data Type: {header['data type']}\n")
    output.write(f"Interleave Format: {header['interleave']}\n")
    output.write(f"Byte Order: {header['byte order']}\n")
    output.write(f"File Format: {header['file type']}\n")
    output.write(f"Map Info: {header.get('map info', 'N/A')}\n")
    output.write(f"Coordinate System String: {header.get('coordinate system string', 'N/A')}\n")
    output.write(f"Reflectance Scale Factor: {header.get('reflectance scale factor', 'N/A')}\n")
    output.write(f"Interleave Factor: {header.get('interleave factor', 'N/A')}\n")
    output.write(f"Data Ignore Value: {header.get('data ignore value', 'N/A')}\n")
    if args.full:
        basic = [
            'lines',
            'samples',
            'bands',
            'data type',
            'interleave',
            'byte order',
            'file type',
            'map info',
            'coordinate system string',
            'reflectance scale factor',
            'interleave factor',
            'data ignore value',
        ]
        output.write("Other fields:\n")
        for k in header:
            if k in basic:
                continue
            output.write("- %s: %s\n" % (k, str(header[k])))

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
