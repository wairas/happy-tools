import argparse
import traceback

from seppl import generate_entry_points
from happy.base.registry import HappyRegistry, ENTRYPOINT_PREPROCESSORS, HAPPY_DEFAULT_MODULES
from typing import List


def output_entry_points(modules: List[str] = None):
    """
    Generates and outputs the entry points.

    :param modules: the modules to generate the entry points for
    :type modules: list
    """
    if (modules is None) or (len(modules) == 0):
        modules = HAPPY_DEFAULT_MODULES
    registry = HappyRegistry(default_modules=modules)

    # generate entry points
    entry_points = dict()
    entry_points[ENTRYPOINT_PREPROCESSORS] = list(registry.preprocessors().values())
    print(generate_entry_points(entry_points))


def main():
    parser = argparse.ArgumentParser(
        description='Generates the entry_points section for the plugins.',
        prog="happy-entry-points",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--modules", metavar="PACKAGE", help="The names of the module packages, uses the default ones if not provided.", default=HAPPY_DEFAULT_MODULES, type=str, required=False, nargs="*")
    args = parser.parse_args()
    output_entry_points(args.modules)


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
