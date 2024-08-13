import argparse
import logging
import sys
import traceback

from seppl import split_args, args_to_objects, get_class_name, is_help_requested
from wai.logging import set_logging_level, add_logging_level
from happy.base.app import init_app
from happy.base.registry import REGISTRY, print_help, print_help_all
from happy.readers import HappyDataReader
from happy.preprocessors import Preprocessor, MultiPreprocessor, apply_preprocessor
from happy.writers import HappyDataWriter

PROG = "happy-process-data"


logger = logging.getLogger(PROG)


def default_pipeline() -> str:
    args = [
        "happy-reader -b INPUT_DIR",
        "wavelength-subset -f 60 -t 189",
        "sni",
        "happy-writer -b OUTPUT_DIR",
    ]
    return " ".join(args)


def main():
    init_app()
    args = sys.argv[1:]
    help_requested, help_all, help_plugin = is_help_requested(args)
    if help_requested:
        if help_all:
            print_help_all()
        elif help_plugin is not None:
            print_help(help_plugin)
        else:
            print("usage: " + PROG + " reader [preprocessor(s)] writer [-h|--help|--help-all|--help-plugin NAME] ")
            print("       [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]")
            print()
            print("Processes data using the specified pipeline.")
            print()
            print("readers: " + ", ".join(REGISTRY.happydata_readers().keys()))
            print("preprocessors: " + ", ".join(REGISTRY.preprocessors().keys()))
            print("writers: " + ", ".join(REGISTRY.happydata_writers().keys()))
            print()
            print("optional arguments:")
            print("  -h, --help            show this help message and exit")
            print("  --help-all            show the help for all plugins and exit")
            print("  --help-plugin NAME    show the help for plugin NAME and exit")
            print("  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}")
            print("                        The logging level to use. (default: WARN)")
            print("")
            print()
        sys.exit(0)

    # create pipeline
    plugins = {}
    plugins.update(REGISTRY.happydata_readers())
    plugins.update(REGISTRY.preprocessors())
    plugins.update(REGISTRY.happydata_writers())
    split = split_args(args, list(plugins.keys()))
    objs = args_to_objects(split, plugins, allow_global_options=True)

    parser = argparse.ArgumentParser()
    add_logging_level(parser, short_opt="-V")
    parsed = parser.parse_args(split[""] if ("" in split) else [])
    set_logging_level(logger, parsed.logging_level)

    # check pipeline
    if len(objs) < 2:
        raise Exception("At least a reader and a writer need to be defined!")

    # reader
    if not isinstance(objs[0], HappyDataReader):
        raise Exception("First component in pipeline must be derived from %s, but got: %s"
                        % (get_class_name(HappyDataReader), get_class_name(objs[0])))
    reader = objs.pop(0)

    # writer
    if not isinstance(objs[-1], HappyDataWriter):
        raise Exception("Last component in pipeline must be derived from %s, but got: %s"
                        % (get_class_name(HappyDataWriter), get_class_name(objs[-1])))
    writer = objs.pop(-1)

    # preprocessors
    for i, obj in enumerate(objs):
        if not isinstance(obj, Preprocessor):
            raise Exception("Expected plugin derived from %s but found at #%d: %s"
                            % (get_class_name(Preprocessor), i+1, get_class_name(obj)))
    preprocessors = None
    if len(objs) > 0:
        preprocessors = MultiPreprocessor(preprocessor_list=objs)

    # execute pipeline
    sample_ids = reader.get_sample_ids()
    for i, sample_id in enumerate(sample_ids, start=1):
        logger.info("Processing %d/%d: %s" % (i, len(sample_ids), sample_id))
        data_list = reader.load_data(sample_id)
        for data in data_list:
            if preprocessors is not None:
                processed = apply_preprocessor(data, preprocessors)
                writer.write_data(processed)
            else:
                writer.write_data(data)


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
