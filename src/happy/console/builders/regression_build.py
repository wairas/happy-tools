import argparse
import logging
import os
import traceback

import numpy as np

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.evaluators import PredictionActualHandler, RegressionEvaluator
from happy.models.scikit_spectroscopy import ScikitSpectroscopyModel
from happy.models.sklearn import create_model, REGRESSION_MODEL_MAP
from happy.models.spectroscopy import create_false_color_image
from happy.pixel_selectors import MultiSelector, PixelSelector
from happy.preprocessors import Preprocessor, MultiPreprocessor
from happy.splitters import DataSplits
from happy.writers import CSVTrainingDataWriter


PROG = "happy-scikit-regression-build"

logger = logging.getLogger(PROG)


def default_preprocessors() -> str:
    args = [
        "wavelength-subset -f 60 -t 189",
        "sni",
        "snv",
        "derivative -w 15",
        "pad -W 128 -H 128 -v 0",
    ]
    return " ".join(args)


def default_pixel_selectors() -> str:
    args = [
        "ps-simple -n 64",
    ]
    return " ".join(args)


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified splits and pixel selector.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the Happy Data files', required=True)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data. Either preprocessor command-line(s) or file with one preprocessor command-line per line.', required=False, default=default_preprocessors())
    parser.add_argument('-S', '--pixel_selectors', type=str, help='The pixel selectors to use. Either pixel selector command-line(s) or file with one pixel selector command-line per line.', required=False, default=default_pixel_selectors())
    parser.add_argument('-m', '--regression_method', type=str, default="linearregression", help='Regression method name (e.g., ' + ",".join(REGRESSION_MODEL_MAP.keys()) + ' or full class name)')
    parser.add_argument('-p', '--regression_params', type=str, default="{}", help='JSON string containing regression parameters')
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

    # method
    logger.info("Creating regression method: %s, options: %s" % (args.regression_method, str(args.regression_params)))
    regression_method = create_model(args.regression_method, args.regression_params)

    # splits
    logger.info("Loading splits: %s" % args.splits_file)
    splits = DataSplits.load(args.splits_file)
    train_ids, valid_ids, test_ids = splits.get_train_validation_test_splits(0, 0)

    # pixel selector
    logger.info("Creating pixel selector")
    train_pixel_selectors = MultiSelector(PixelSelector.parse_pixel_selectors(args.pixel_selectors))

    # preprocessing
    logger.info("Creating pre-processing")
    preproc = MultiPreprocessor(preprocessor_list=Preprocessor.parse_preprocessors(args.preprocessors))

    # model
    model = ScikitSpectroscopyModel(args.happy_data_base_dir, args.target_value, happy_preprocessor=preproc, additional_meta_data=None, pixel_selector=train_pixel_selectors, model=regression_method, training_data=None)
    logger.info("Fitting model...")
    model.fit(train_ids, force=True, keep_training_data=False)
    
    csv_writer = CSVTrainingDataWriter(args.output_folder)
    csv_writer.write_data(model.get_training_data(), "training_data")

    logger.info("Predicting...")
    predictions, actuals = model.predict_images(test_ids, return_actuals=True)
    
    evl = RegressionEvaluator(splits, model, args.target_value)

    predictions = PredictionActualHandler.to_list(predictions, remove_last_dim=True)
    actuals = PredictionActualHandler.to_list(actuals, remove_last_dim=True)
    logger.info(f"predictions.shape:{predictions[0].shape}  actuals.shape:{actuals[0].shape}")
    
    flat_actuals = np.concatenate(actuals).flatten()
    max_actual = np.nanmax(flat_actuals)
    min_actual = np.nanmin(flat_actuals)

    # Save the predictions as PNG images
    for i, prediction in enumerate(predictions):
        evl.accumulate_stats(np.array(predictions[i]), actuals[i], 0, 0)
        if np.isnan(min_actual) or np.isnan(max_actual) or (min_actual == max_actual):
            logger.warning("NaN value detected. Cannot proceed with gradient calculation.")
            continue
        false_color_image = create_false_color_image(prediction, min_actual, max_actual)
        false_color_image.save(os.path.join(args.output_folder, f'false_color_{i}.png'))
    evl.calculate_and_show_metrics()


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
