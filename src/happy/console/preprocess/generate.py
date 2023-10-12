import argparse
import traceback

from seppl import split_args, split_cmdline, args_to_objects, get_class_name
from happy.base.registry import REGISTRY
from happy.readers import HappyDataReader
from happy.preprocessors import Preprocessor, MultiPreprocessor
from happy.writers import HappyDataWriter


def default_pipeline() -> str:
    args = [
        "happy-reader -b input_dir",
        "wavelength-subset -f 60 -t 189",
        "sni",
        "happy-writer -b output_dir",
    ]
    return " ".join(args)


def main():
    parser = argparse.ArgumentParser(
        description="Preprocesses data using the specified pipeline ('reader [preprocessor(s)] writer').",
        prog="happy-preprocess",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', "--pipeline", type=str, help="The processing pipeline: reader [preprocessor(s)] writer, e.g.: " + default_pipeline(), required=True, default=None)
    args = parser.parse_args()

    # create pipeline
    plugins = {}
    plugins.update(REGISTRY.happydata_readers())
    plugins.update(REGISTRY.preprocessors())
    plugins.update(REGISTRY.happydata_writers())
    split = split_args(split_cmdline(args.pipeline), list(plugins.keys()))
    objs = args_to_objects(split, plugins, allow_global_options=False)

    # check pipeline
    if len(objs) < 2:
        raise Exception("At least a read and a writer need to be defined!")

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
    preprocessors = MultiPreprocessor(preprocessor_list=objs)

    # execute pipeline
    for sample_id in reader.get_sample_ids():
        print(sample_id)
        data = reader.load_data(sample_id)
        preprocessed = preprocessors.apply(data)
        writer.write_data(preprocessed)


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
