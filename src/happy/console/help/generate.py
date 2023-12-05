import argparse
import os
import traceback

from seppl import generate_help, HELP_FORMATS, HELP_FORMAT_TEXT, HELP_FORMAT_MARKDOWN
from happy.base.registry import HappyRegistry, HAPPY_DEFAULT_MODULES
from typing import List


def _add_plugins_to_index(heading: str, plugins: dict, help_format: str, lines: list):
    """
    Appends a plugin section to the output list.

    :param heading: the heading of the section
    :type heading: str
    :param plugins: the plugins dictionary to add
    :type plugins: dict
    :param help_format: the type of output to generate
    :type help_format: str
    :param lines: the output lines to append the output to
    :type lines: list
    """
    plugin_names = sorted(plugins.keys())
    if len(plugin_names) == 0:
        return
    if help_format == HELP_FORMAT_MARKDOWN:
        lines.append("## " + heading)
        for name in plugin_names:
            lines.append("* [%s](%s.md)" % (name, name))
        lines.append("")
    elif help_format == HELP_FORMAT_TEXT:
        lines.append(heading)
        lines.append("-" * len(heading))
        for name in plugin_names:
            lines.append("- %s" % name)
        lines.append("")
    else:
        raise Exception("Unsupported format for index: %s" % help_format)


def output_help(modules: List[str] = None, help_format: str = HELP_FORMAT_TEXT, heading_level: int = 1,
                output_path: str = None, index: str = None):
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
    :param index: the index file to generate in the output directory, ignored if None
    :type index: str
    """
    if (modules is None) or (len(modules) == 0):
        modules = HAPPY_DEFAULT_MODULES
    registry = HappyRegistry(default_modules=modules)
    generate_help(list(registry.all_plugins().values()), help_format=help_format, heading_level=heading_level,
                  output_path=output_path)

    if index is not None:
        # reset registry
        registry = HappyRegistry(default_modules=modules)
        header_lines = []
        if help_format == HELP_FORMAT_MARKDOWN:
            header_lines.append("# HAPPy plugins")
            header_lines.append("")
        elif help_format == HELP_FORMAT_TEXT:
            heading = "HAPPy plugins"
            header_lines.append(heading)
            header_lines.append("=" * len(heading))
            header_lines.append("")
        else:
            raise Exception("Unsupported format for index: %s" % help_format)
        plugin_lines = []
        _add_plugins_to_index("Black reference methods", registry.blackref_methods(), help_format, plugin_lines)
        _add_plugins_to_index("White reference methods", registry.whiteref_methods(), help_format, plugin_lines)
        _add_plugins_to_index("Reference locators", registry.ref_locators(), help_format, plugin_lines)
        _add_plugins_to_index("HAPPY data readers", registry.happydata_readers(), help_format, plugin_lines)
        _add_plugins_to_index("HAPPY data preprocessors", registry.preprocessors(), help_format, plugin_lines)
        _add_plugins_to_index("HAPPY data writers", registry.happydata_writers(), help_format, plugin_lines)
        _add_plugins_to_index("Pixel selectors", registry.pixel_selectors(), help_format, plugin_lines)
        _add_plugins_to_index("Region extractors", registry.region_extractors(), help_format, plugin_lines)
        if len(plugin_lines) < 0:
            print("No plugins listed, skipping output of index file.")
        else:
            index_file = os.path.join(output_path, index)
            os.makedirs(os.path.dirname(index_file), exist_ok=True)
            with open(index_file, "w") as fp:
                fp.write("\n".join(header_lines))
                fp.write("\n".join(plugin_lines))


def main():
    parser = argparse.ArgumentParser(
        description='Generates the help screens for the plugins.',
        prog="happy-help",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--modules", metavar="PACKAGE", help="The names of the module packages, uses the default ones if not provided.", default=HAPPY_DEFAULT_MODULES.split(","), type=str, required=False, nargs="*")
    parser.add_argument("-f", "--help_format", metavar="FORMAT", help="The output format to generate", choices=HELP_FORMATS, default=HELP_FORMAT_TEXT, required=False)
    parser.add_argument("-L", "--heading_level", metavar="INT", help="The level to use for the heading", default=1, type=int, required=False)
    parser.add_argument("-o", "--output", metavar="PATH", help="The directory to store the help in; outputs it to stdout if not supplied; automatically generates file name from plugin name and help format", type=str, default=None, required=False)
    parser.add_argument("-i", "--index", metavar="FILE", help="The file in the output directory to generate with an overview of all plugins, grouped by type (in markdown format, links them to the other generated files)", type=str, default=None, required=False)
    parsed = parser.parse_args()
    output_help(modules=parsed.modules, help_format=parsed.help_format, heading_level=parsed.heading_level,
                output_path=parsed.output, index=parsed.index)


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
