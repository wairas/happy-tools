#!/usr/bin/python3
import argparse
import logging
import os
import traceback

from PIL import Image
from wai.logging import add_logging_level, set_logging_level

from happy.base.app import init_app
from happy.data import DataManager
from happy.data.black_ref import AbstractBlackReferenceMethod
from happy.data.ref_locator import AbstractReferenceLocator
from happy.data.white_ref import AbstractWhiteReferenceMethod


PROG = "happy-hsi2rgb"

logger = logging.getLogger(PROG)


def log(msg):
    """
    For logging messages.

    :param msg: the message to print
    """
    logger.info(msg)


def convert(input_path, output_path, datamanager,
            autodetect_channels=True, red_channel=0, green_channel=0, blue_channel=0,
            width=None, height=None, dry_run=False):
    """
    Converts the specified file.

    :param input_path: the HSI image to convert
    :type input_path: str
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
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
    """
    log("- %s" % input_path)

    datamanager.load_scan(input_path)

    if autodetect_channels:
        try:
            metadata = datamanager.scan_img.metadata
            if "default bands" in metadata:
                bands = [int(x) for x in metadata["default bands"]]
                log("  using default bands: %s" % str(bands))
                red_channel, green_channel, blue_channel = bands
        except:
            pass

    datamanager.update_image(red_channel, green_channel, blue_channel)
    image = Image.fromarray(datamanager.display_image)
    act_width, act_height = image.size
    if width > 0:
        act_width = width
    if height > 0:
        act_height = height
    image = image.resize((act_width, act_height), Image.LANCZOS)
    log("  --> %s" % output_path)
    if not dry_run:
        image.save(output_path)


def generate(input_dirs, datamanager, extension=".hdr",
             autodetect_channels=True, red_channel=0, green_channel=0, blue_channel=0,
             recursive=False, output_dir=None, width=None, height=None,
             dry_run=False, excluded=None):
    """
    Generates fake RGB images from the HSI images found in the specified directories.

    :param input_dirs: the input dir(s) to traverse
    :type input_dirs: str or list
    :param datamanager: the data manager instance to use
    :type datamanager: DataManager
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
    :param excluded: set of excluded files
    :type excluded: set
    """

    if isinstance(input_dirs, str):
        input_dirs = [input_dirs]

    if excluded is None:
        excluded = set()

    for input_dir in input_dirs:
        log("Entering: %s" % input_dir)

        for f in os.listdir(input_dir):
            input_path = os.path.join(input_dir, f)

            if input_path in excluded:
                continue

            if recursive and os.path.isdir(input_path):
                generate(input_path, datamanager, extension=extension,
                         autodetect_channels=autodetect_channels,
                         red_channel=red_channel, green_channel=green_channel, blue_channel=blue_channel,
                         recursive=True, output_dir=output_dir, width=width, height=height,
                         dry_run=dry_run, excluded=excluded)

            if f.endswith(extension):
                if output_dir is None:
                    output_path = os.path.join(input_dir, os.path.splitext(f)[0] + ".png")
                else:
                    output_path = os.path.join(output_dir, os.path.splitext(f)[0] + ".png")
                convert(input_path, output_path, datamanager,
                        autodetect_channels=autodetect_channels,
                        red_channel=red_channel, green_channel=green_channel, blue_channel=blue_channel,
                        width=width, height=height, dry_run=dry_run)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    init_app()
    parser = argparse.ArgumentParser(
        description="Fake RGB image generator for HSI files.",
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_dir", nargs="+", type=str, help="Path to the scan file (ENVI format)", required=True)
    parser.add_argument("-r", "--recursive", action="store_true", help="whether to traverse the directories recursively", required=False)
    parser.add_argument("-e", "--extension", type=str, help="The file extension to look for", default=".hdr", required=False)
    parser.add_argument("--black_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating black references, eg rl-manual", default=None, required=False)
    parser.add_argument("--black_ref_method", metavar="METHOD", help="the black reference method to use for applying black references, eg br-same-size", default=None, required=False)
    parser.add_argument("--white_ref_locator", metavar="LOCATOR", help="the reference locator scheme to use for locating whites references, eg rl-manual", default=None, required=False)
    parser.add_argument("--white_ref_method", metavar="METHOD", help="the white reference method to use for applying white references, eg wr-same-size", default=None, required=False)
    parser.add_argument("-a", "--autodetect_channels", action="store_true", help="whether to determine the channels from the meta-data (overrides the manually specified channels)", required=False)
    parser.add_argument("--red", metavar="INT", help="the wave length to use for the red channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("--green", metavar="INT", help="the wave length to use for the green channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("--blue", metavar="INT", help="the wave length to use for the blue channel (0-based)", default=0, type=int, required=False)
    parser.add_argument("-o", "--output_dir", type=str, help="The directory to store the fake RGB PNG images instead of alongside the HSI images.", required=False)
    parser.add_argument("--width", metavar="INT", help="the width to scale the images to (<= 0 uses image dimension)", default=0, type=int, required=False)
    parser.add_argument("--height", metavar="INT", help="the height to scale the images to (<= 0 uses image dimension)", default=0, type=int, required=False)
    parser.add_argument("-n", "--dry_run", action="store_true", help="whether to omit saving the PNG images", required=False)
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(args=args)

    set_logging_level(logger, parsed.logging_level)

    black_ref_locator = None
    black_ref_method = None
    white_ref_locator = None
    white_ref_method = None
    if parsed.black_ref_locator is not None:
        black_ref_locator = AbstractReferenceLocator.parse_locator(parsed.black_ref_locator)
    if parsed.black_ref_method is not None:
        black_ref_method = AbstractBlackReferenceMethod.parse_method(parsed.black_ref_method)
    if parsed.white_ref_locator is not None:
        white_ref_locator = AbstractReferenceLocator.parse_locator(parsed.white_ref_locator)
    if parsed.white_ref_method is not None:
        white_ref_method = AbstractWhiteReferenceMethod.parse_method(parsed.white_ref_method)

    datamanager = DataManager(log_method=log)
    datamanager.set_blackref_locator(black_ref_locator)
    datamanager.set_blackref_method(black_ref_method)
    datamanager.set_whiteref_locator(white_ref_locator)
    datamanager.set_whiteref_method(white_ref_method)

    generate(parsed.input_dir, datamanager,
             extension=parsed.extension, autodetect_channels=parsed.autodetect_channels,
             red_channel=parsed.red, green_channel=parsed.green, blue_channel=parsed.blue,
             recursive=parsed.recursive, output_dir=parsed.output_dir, width=parsed.width, height=parsed.height,
             dry_run=parsed.dry_run)


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
