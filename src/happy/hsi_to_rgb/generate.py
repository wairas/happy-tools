#!/usr/bin/python3
import argparse
import spectral.io.envi as envi
import numpy as np
import os
import traceback

from PIL import Image


def normalize_data(data):
    """
    Normalizes data.

    :param data: the data to normalize
    :return: the normalized data
    """
    min_value = np.min(data)
    max_value = np.max(data)
    data_range = max_value - min_value

    if data_range == 0:  # Handle division by zero
        data = np.zeros_like(data)
    else:
        data = (data - min_value) / data_range
    return data


def convert(input_path, output_path, black_reference=None, white_reference=None,
            autodetect_channels=True, red_channel=0, green_channel=0, blue_channel=0,
            width=None, height=None, dry_run=False, verbose=False):
    """
    Converts the specified file.

    :param input_path: the HSI image to convert
    :type input_path: str
    :param black_reference: the (optional) black reference to use
    :type black_reference: str or ENVI object
    :param white_reference: the (optional) white reference to use
    :type white_reference: str or ENVI object
    :param output_path: the PNG image to generate
    :type output_path: str
    :param autodetect_channels: whether to use the default bands as default channels (if present)
    :type autodetect_channels: bool
    :param red_channel: the band to use as red channel (0-based)
    :type red_channel: int
    :param green_channel: the band to use as green channel (0-based)
    :type green_channel: int
    :param blue_channel: the band to use as blue channel (0-based)
    :type blue_channel: int
    :param width: the fixed width to scale the images to (<= 0 uses image dimension)
    :type width: int
    :param height: the fixed height to scale the images to (<= 0 uses image dimension)
    :type height: int
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    """
    if verbose:
        print("- %s" % input_path)

    img = envi.open(input_path)
    data_scan = img.load()
    
    if autodetect_channels:
        try:
            metadata = img.metadata
            if "default bands" in metadata:
                bands = [int(x) for x in metadata["default bands"]]
                if verbose:
                    print("  using default bands: %s" % str(bands))
                red_channel, green_channel, blue_channel = bands
        except:
            pass

    if black_reference is not None:
        if data_scan.shape != black_reference.shape:
            print("  WARNING: Dimensions of scan and black reference differ: %s != %s "
                  % (str(data_scan.shape), str(black_reference.shape)))
            black_reference = None
            white_reference = None

    data_norm = data_scan
    # subtract black reference
    if black_reference is not None:
        data_norm = data_norm - black_reference
    # divide by white reference
    if white_reference is not None:
        data_norm = data_norm / white_reference

    red_band = data_norm[:, :, red_channel]
    green_band = data_norm[:, :, green_channel]
    blue_band = data_norm[:, :, blue_channel]

    norm_red = normalize_data(red_band)
    norm_green = normalize_data(green_band)
    norm_blue = normalize_data(blue_band)

    rgb_image = np.dstack((norm_red, norm_green, norm_blue))
    display_image = (rgb_image * 255).astype(np.uint8)

    image = Image.fromarray(display_image)
    act_width, act_height = image.size
    if width > 0:
        act_width = width
    if height > 0:
        act_height = height
    image = image.resize((act_width, act_height), Image.LANCZOS)
    if verbose:
        print("  --> %s" % output_path)
    if not dry_run:
        image.save(output_path)


def generate(input_dirs, black_reference=None, white_reference=None, extension=".hdr",
             autodetect_channels=True, red_channel=0, green_channel=0, blue_channel=0,
             recursive=False, output_dir=None, width=None, height=None,
             dry_run=False, verbose=False, excluded=None):
    """
    Generates fake RGB images from the HSI images found in the specified directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param black_reference: the (optional) black reference to use
    :type black_reference: str or ENVI object
    :param white_reference: the (optional) white reference to use
    :type white_reference: str or ENVI object
    :param extension: the extension (incl dot) that the HSI images must have
    :type extension: str
    :param autodetect_channels: whether to use the default bands as default channels (if present)
    :type autodetect_channels: bool
    :param red_channel: the band to use as red channel (0-based)
    :type red_channel: int
    :param green_channel: the band to use as green channel (0-based)
    :type green_channel: int
    :param blue_channel: the band to use as blue channel (0-based)
    :type blue_channel: int
    :param recursive: whether to traverse the input dir(s) recursively or not
    :type recursive: bool
    :param output_dir: the (optional) output directory to place the generated PNG images in instead of alongside HSI images
    :type output_dir: str
    :param width: the fixed width to scale the images to (<= 0 uses image dimension)
    :type width: int
    :param height: the fixed height to scale the images to (<= 0 uses image dimension)
    :type height: int
    :param dry_run: whether to omit saving the PNG images
    :type dry_run: bool
    :param verbose: whether to be more verbose with the output
    :type verbose: bool
    :param excluded: set of excluded files
    :type excluded: set
    """

    if isinstance(input_dirs, str):
        input_dirs = [input_dirs]

    if excluded is None:
        excluded = set()

    if black_reference is not None:
        if isinstance(black_reference, str):
            print("Loading black reference: %s" % black_reference)
            excluded.add(black_reference)
            black_reference = envi.open(black_reference).load()

    if white_reference is not None:
        if isinstance(white_reference, str):
            print("Loading white reference: %s" % white_reference)
            excluded.add(white_reference)
            white_reference = envi.open(white_reference).load()

    if (black_reference is not None) and (white_reference is not None):
        if black_reference.shape != white_reference.shape:
            raise Exception("Dimensions of black and white reference differ: %s != %s"
                            % (str(black_reference.shape), str(white_reference.shape)))

    for input_dir in input_dirs:
        print("Entering: %s" % input_dir)

        for f in os.listdir(input_dir):
            input_path = os.path.join(input_dir, f)

            if input_path in excluded:
                continue

            if recursive and os.path.isdir(input_path):
                generate(input_path, black_reference=black_reference, white_reference=white_reference, extension=extension,
                         autodetect_channels=autodetect_channels,
                         red_channel=red_channel, green_channel=green_channel, blue_channel=blue_channel,
                         recursive=True, output_dir=output_dir, width=width, height=height,
                         dry_run=dry_run, verbose=verbose, excluded=excluded)

            if f.endswith(extension):
                if output_dir is None:
                    output_path = os.path.join(input_dir, os.path.splitext(f)[0] + ".png")
                else:
                    output_path = os.path.join(output_dir, os.path.splitext(f)[0] + ".png")
                convert(input_path, output_path, black_reference=black_reference, white_reference=white_reference,
                        autodetect_channels=autodetect_channels,
                        red_channel=red_channel, green_channel=green_channel, blue_channel=blue_channel,
                        width=width, height=height, dry_run=dry_run, verbose=verbose)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="Fake RGB image generator for HSI files.",
        prog="happy-hsi2rgb",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", type=str, help="Path to the scan file (ENVI format)", required=True)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to traverse the directories recursively", required=False)
    parser.add_argument("-e", "--extension", type=str, help="The file extension to look for", default=".hdr", required=False)
    parser.add_argument("-b", "--black_reference", type=str, help="Path to the black reference file (ENVI format)", required=False)
    parser.add_argument("-w", "--white_reference", type=str, help="Path to the white reference file (ENVI format)", required=False)
    parser.add_argument("-a", "--autodetect_channels", action="store_true", help="whether to determine the channels from the meta-data (overrides the manually specified channels)", required=False)
    parser.add_argument("--red", metavar="INT", help="the wave length to use for the red channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("--green", metavar="INT", help="the wave length to use for the green channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("--blue", metavar="INT", help="the wave length to use for the blue channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("-o", "--output_dir", type=str, help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("--width", metavar="INT", help="the width to scale the images to (<= 0 uses image dimension)", default=0, type=int, required=False)
    parser.add_argument("--height", metavar="INT", help="the height to scale the images to (<= 0 uses image dimension)", default=0, type=int, required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit saving the PNG images", required=False)
    parser.add_argument("-v", "--verbose", action="store_true", help="whether to be more verbose with the output", required=False)
    parsed = parser.parse_args(args=args)
    generate(parsed.input_dir, black_reference=parsed.black_reference, white_reference=parsed.white_reference,
             extension=parsed.extension, autodetect_channels=parsed.autodetect_channels,
             red_channel=parsed.red, green_channel=parsed.green, blue_channel=parsed.blue,
             recursive=parsed.recursive, output_dir=parsed.output_dir, width=parsed.width, height=parsed.height,
             dry_run=parsed.dry_run, verbose=parsed.verbose)


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
