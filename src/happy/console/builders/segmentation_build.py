import argparse
import logging
import os
import traceback

import numpy as np

from wai.logging import add_logging_level, set_logging_level
from happy.evaluators import ClassificationEvaluator
from happy.models.scikit_spectroscopy import ScikitSpectroscopyModel
from happy.models.sklearn import create_model, CLASSIFICATION_MODEL_MAP
from happy.pixel_selectors import MultiSelector, PixelSelector
from happy.preprocessors import Preprocessor, MultiPreprocessor
from happy.splitters import HappySplitter
from happy.writers import CSVTrainingDataWriter
from happy.models.segmentation import create_false_color_image, create_prediction_image
from happy.writers import EnviWriter


PROG = "happy-scikit-regression-build"

logger = logging.getLogger(PROG)


def default_preprocessors() -> str:
    args = [
    ]
    return " ".join(args)


def default_pixel_selectors() -> str:
    args = [
        "simple-ps -n 32767",
    ]
    return " ".join(args)


def one_hot(arr, num_classes):
    # Determine the dimensions of raw_y
    height, width = arr.shape[0], arr.shape[1]

    # Turn raw_y into one-hot encoding
    one_hot = np.eye(num_classes)[arr.reshape(-1)]
    one_hot = one_hot.reshape((height, width, num_classes))

    logger.info(f"raw_y-shape: {arr.shape}")
    logger.info(f"one_hot-shape: {one_hot.shape}")
    return one_hot


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
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified splits and pixel selector.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the Happy Data files', required=True)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data', required=False, default=default_preprocessors())
    parser.add_argument('-S', '--pixel_selectors', type=str, help='The pixel selectors to use.', required=False, default=default_pixel_selectors())
    parser.add_argument('-m', '--regression_method', type=str, default="svm", help='Regression method name (e.g., ' + ",".join(CLASSIFICATION_MODEL_MAP.keys()) + ' or full class name)')
    parser.add_argument('-n', '--num_classes', type=int, default=4, help='The number of classes, used for generating the mapping')
    parser.add_argument('-p', '--regression_params', type=str, default="{}", help='JSON string containing regression parameters')
    parser.add_argument('-t', '--target_value', type=str, help='Target value column name', required=True)
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')
    add_logging_level(parser, short_opt="-V")

    args = parser.parse_args()
    set_logging_level(logger, args.logging_level)

    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    regression_method = create_model(args.regression_method, args.regression_params)
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0,0)
    
    train_pixel_selectors = MultiSelector(PixelSelector.parse_pixel_selectors(args.pixel_selectors))

    # preprocessing
    preproc = MultiPreprocessor(preprocessor_list=Preprocessor.parse_preprocessors(args.preprocessors))

    mapping = {}
    num_labels = args.num_classes
    # there is an optional mapping file in happy data now, but TODO here.
    for i in range(args.num_classes):
        mapping[i] = i
    # model
    model = ScikitSpectroscopyModel(args.happy_data_base_dir, args.target_value, happy_preprocessor=preproc, additional_meta_data=None, pixel_selector=train_pixel_selectors, model=regression_method, training_data = None, mapping=mapping)
    model.fit(train_ids, force=True, keep_training_data=False)
    
    csv_writer = CSVTrainingDataWriter(args.output_folder)
    csv_writer.write_data(model.get_training_data(), "training_data")

    predictions, actuals = model.predict_images(test_ids, return_actuals=True)
    predictions = one_hot_list(predictions, num_labels)
    actuals = one_hot_list(actuals, num_labels)
    logger.info(predictions.shape)
    logger.info(actuals.shape)
    evl = ClassificationEvaluator(happy_splitter, model, args.target_value)
    evl.accumulate_stats(predictions, actuals, 0, 0)
    evl.calculate_and_show_metrics()

    # Save the predictions as PNG images
    for i, prediction in enumerate(predictions):
        prediction_array = create_prediction_array(prediction)
        file_path = os.path.join(args.output_folder, f"{i}.hdr")
        envi_writer = EnviWriter(os.path.join(args.output_folder))
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
