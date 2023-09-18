import argparse
import spectral.io.envi as envi
import traceback


def main():
    parser = argparse.ArgumentParser(
        description='Load and print information about an HDR file.',
        prog="happy-hdr-info",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('hdrfile', type=str, help='Path to the HDR file')
    args = parser.parse_args()

    header = envi.read_envi_header(args.hdrfile)

    print("Header Information:")
    print(f"Dimensions: {header['lines']} x {header['samples']}")
    print(f"Number of Bands: {header['bands']}")
    print(f"Data Type: {header['data type']}")
    print(f"Interleave Format: {header['interleave']}")
    print(f"Byte Order: {header['byte order']}")
    print(f"File Format: {header['file type']}")
    print(f"Map Info: {header.get('map info', 'N/A')}")
    print(f"Coordinate System String: {header.get('coordinate system string', 'N/A')}")
    print(f"Reflectance Scale Factor: {header.get('reflectance scale factor', 'N/A')}")
    print(f"Interleave Factor: {header.get('interleave factor', 'N/A')}")
    print(f"Data Ignore Value: {header.get('data ignore value', 'N/A')}")


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
