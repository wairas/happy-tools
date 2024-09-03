import argparse
import logging
import os
import traceback

import numpy as np

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.evaluators import ClassificationEvaluator
from happy.models.scikit_spectroscopy import ScikitSpectroscopyModel
from happy.models.sklearn import create_model, CLASSIFICATION_MODEL_MAP
from happy.pixel_selectors import MultiSelector, PixelSelector
from happy.preprocessors import Preprocessor, MultiPreprocessor
from happy.splitters import DataSplits
from happy.writers.base import CSVTrainingDataWriter, EnviWriter
from happy.models.segmentation import create_false_color_image, create_prediction_image
from happy.data import determine_label_indices, check_labels


PROG = "happy-scikit-segmentation-build"

logger = logging.getLogger(PROG)


def default_preprocessors() -> str:
    args = [
    ]
    return " ".join(args)


def default_pixel_selectors() -> str:
    args = [
        "ps-simple -n 32767",
    ]
    return " ".join(args)


def one_hot(arr, num_classes):
    if np.max(arr) + 1 > num_classes:
        raise Exception("Mismatch between #classes and max+1: %d != %d (unique values: %s)" % (num_classes, np.max(arr)+1, str(np.unique(arr))))

    # Determine the dimensions of raw_y
    height, width = arr.shape[0], arr.shape[1]

    # Turn raw_y into one-hot encoding
    result = np.eye(num_classes)[arr.reshape(-1)]
    result = result.reshape((height, width, num_classes))

    logger.info(f"raw_y-shape: {arr.shape}")
    logger.info(f"one_hot-shape: {result.shape}")
    return result


def one_hot_list(list_of_arrays, num_classes):
    one_hot_encoded_list = [one_hot(arr, num_classes) for arr in list_of_arrays]

    # Convert the list of arrays to a NumPy array
    one_hot_encoded_array = np.array(one_hot_encoded_list)

    return one_hot_encoded_array


def create_prediction_array(prediction):
    # Create a grayscale prediction image
    prediction = np.argmax(prediction, axis=-1)
    prediction_array = prediction.astype(np.uint8)
    return prediction_array


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Evaluate segmentation model on Happy Data using specified splits and pixel selector.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the Happy Data files', required=True)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data', required=False, default=default_preprocessors())
    parser.add_argument('-S', '--pixel_selectors', type=str, help='The pixel selectors to use.', required=False, default=default_pixel_selectors())
    parser.add_argument('-m', '--segmentation_method', type=str, default="svm", help='Segmentation method name (e.g., ' + ",".join(CLASSIFICATION_MODEL_MAP.keys()) + ' or full class name)')
    parser.add_argument('-p', '--segmentation_params', type=str, default="{}", help='JSON string containing segmentation parameters')
    parser.add_argument('-t', '--target_value', type=str, help='Target value column name', required=True)
    parser.add_argument('-s', '--splits_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')
    add_logging_level(parser, short_opt="-V")

    args = parser.parse_args()
    set_logging_level(logger, args.logging_level)

    # Create the output folder if it doesn't exist
    logger.info("Creating output dir: %s" % args.output_folder)
    os.makedirs(args.output_folder, exist_ok=True)

    # creating regression method
    logger.info("Creating segmentation method: %s, options: %s" % (args.segmentation_method, str(args.segmentation_params)))
    regression_method = create_model(args.segmentation_method, args.segmentation_params)

    # split
    logger.info("Loading splits: %s" % args.splits_file)
    splits = DataSplits.load(args.splits_file)
    train_ids, valid_ids, test_ids = splits.get_train_validation_test_splits(0, 0)

    # pixel selector
    logger.info("Creating pixel selector")
    train_pixel_selectors = MultiSelector(PixelSelector.parse_pixel_selectors(args.pixel_selectors))

    # preprocessing
    logger.info("Creating pre-processing")
    preproc = MultiPreprocessor(preprocessor_list=Preprocessor.parse_preprocessors(args.preprocessors))

    # determine #classes from labels files
    logger.info("Determining mapping")
    labels_ok = check_labels(args.happy_data_base_dir)
    logger.info("labels OK: %s" % str(labels_ok))
    indices = determine_label_indices(args.happy_data_base_dir)
    logger.info("label indices: %s" % str(indices))
    mapping = {}
    num_labels = len(indices)
    for i in range(num_labels):
        mapping[i] = i

    # model
    model = ScikitSpectroscopyModel(args.happy_data_base_dir, args.target_value, happy_preprocessor=preproc, additional_meta_data=None, pixel_selector=train_pixel_selectors, model=regression_method, training_data=None, mapping=mapping)
    logger.info("Fitting model...")
    model.fit(train_ids, force=True, keep_training_data=False)
    
    csv_writer = CSVTrainingDataWriter(args.output_folder)
    csv_writer.logging_level = args.logging_level
    csv_writer.write_data(model.get_training_data(), "training_data")

    logger.info("Predicting...")
    predictions, actuals = model.predict_images(test_ids, return_actuals=True)
    actuals = one_hot_list(actuals, num_labels)
    predictions = one_hot_list(predictions, num_labels)
    logger.info(predictions.shape)
    logger.info(actuals.shape)
    evl = ClassificationEvaluator(splits, model, args.target_value)
    evl.accumulate_stats(predictions, actuals, 0, 0)
    evl.calculate_and_show_metrics()

    # Save the predictions as PNG images
    for i, prediction in enumerate(predictions):
        prediction_array = create_prediction_array(prediction)
        file_path = os.path.join(args.output_folder, f"{i}.hdr")
        envi_writer = EnviWriter(os.path.join(args.output_folder))
        envi_writer.logging_level = args.logging_level
        envi_writer.write_data(prediction_array, file_path)

        prediction_image = create_prediction_image(prediction)
        prediction_image.save(os.path.join(args.output_folder, f'prediction_{i}.png'))

        false_color_image = create_false_color_image(prediction, mapping)
        false_color_image.save(os.path.join(args.output_folder, f'false_color_{i}.png'))


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
