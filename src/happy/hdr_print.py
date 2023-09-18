import argparse
import spectral.io.envi as envi

def main():
    parser = argparse.ArgumentParser(description='Load and print information about an HDR file.')
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

if __name__ == "__main__":
    main()
