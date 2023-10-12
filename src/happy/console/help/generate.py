import argparse
import traceback

from seppl import generate_help, HELP_FORMATS, HELP_FORMAT_TEXT
from happy.base.registry import HappyRegistry, HAPPY_DEFAULT_MODULES
from happy.base.registry import ENTRYPOINT_PREPROCESSORS, ENTRYPOINT_HAPPYDATA_READERS, ENTRYPOINT_HAPPYDATA_WRITERS, \
    ENTRYPOINT_PIXEL_SELECTORS, ENTRYPOINT_REGION_EXTRACTORS
from typing import List


def output_help(modules: List[str] = None, help_format: str = HELP_FORMAT_TEXT, heading_level: int = 1,
                output_path: str = None):
    """
    Generates and outputs the help screens for the plugins.

    :param modules: the modules to generate the entry points for
    :type modules: list
    :param help_format: the format to output
    :type help_format: str
    :param heading_level: the heading level to use (markdown)
    :type heading_level: int
    :param output_path: the dir to save the output to, uses stdout if None
    :type output_path: str
    """
    if (modules is None) or (len(modules) == 0):
        modules = HAPPY_DEFAULT_MODULES
    registry = HappyRegistry(default_modules=modules)

    # generate entry points
    entry_points = dict()
    entry_points[ENTRYPOINT_PREPROCESSORS] = list(registry.preprocessors().values())
    entry_points[ENTRYPOINT_HAPPYDATA_READERS] = list(registry.happydata_readers().values())
    entry_points[ENTRYPOINT_HAPPYDATA_WRITERS] = list(registry.happydata_writers().values())
    entry_points[ENTRYPOINT_PIXEL_SELECTORS] = list(registry.pixel_selectors().values())
    entry_points[ENTRYPOINT_REGION_EXTRACTORS] = list(registry.region_extractors().values())
    generate_help(list(registry.preprocessors().values()), help_format=help_format, heading_level=heading_level,
                  output_path=output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generates the help screens for the plugins.',
        prog="happy-help",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--modules", metavar="PACKAGE", help="The names of the module packages, uses the default ones if not provided.", default=HAPPY_DEFAULT_MODULES.split(","), type=str, required=False, nargs="*")
    parser.add_argument("-f", "--help_format", metavar="FORMAT", help="The output format to generate", choices=HELP_FORMATS, default=HELP_FORMAT_TEXT, required=False)
    parser.add_argument("-L", "--heading_level", metavar="INT", help="The level to use for the heading", default=1, type=int, required=False)
    parser.add_argument("-o", "--output", metavar="PATH", help="The directory to store the help in; outputs it to stdout if not supplied; automatically generates file name from plugin name and help format", type=str, default=None, required=False)
    args = parser.parse_args()
    output_help(modules=args.modules, help_format=args.help_format, heading_level=args.heading_level, output_path=args.output)


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
