import argparse
import logging
import os
import time
import traceback

import numpy as np

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.base.core import load_class
from happy.evaluators import PredictionActualHandler, RegressionEvaluator
from happy.models.generic import GenericSpectroscopyModel, GenericScikitSpectroscopyModel
from happy.models.spectroscopy import create_false_color_image, SpectroscopyModel
from happy.models.scikit_spectroscopy import ScikitSpectroscopyModel
from happy.splitters import HappySplitter
from happy.writers import CSVTrainingDataWriter


PROG = "happy-generic-regression-build"

logger = logging.getLogger(PROG)


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified class from Python module.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the HAPPy data')
    parser.add_argument('-P', '--python_file', type=str, help='The Python module with the model class to load')
    parser.add_argument('-c', '--python_class', type=str, help='The name of the model class to load')
    parser.add_argument('-t', '--target_value', type=str, help='Target value column name')
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file')
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions')
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 1)')
    add_logging_level(parser, short_opt="-V")

    args = parser.parse_args()
    set_logging_level(logger, args.logging_level)

    # Create the output folder if it doesn't exist
    logger.info("Creating output dir: %s" % args.output_folder)
    os.makedirs(args.output_folder, exist_ok=True)

    # splits
    logger.info("Loading splits: %s" % args.happy_splitter_file)
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0, 0)

    # method
    logger.info("Loading class %s from: %s" % (args.python_class, args.python_file))
    c = load_class(args.python_file, "happy.generic_regression." + str(int(round(time.time() * 1000))), args.python_class)
    if issubclass(c, ScikitSpectroscopyModel):
        model = GenericScikitSpectroscopyModel.instantiate(c, args.happy_data_base_dir, args.target_value)
    elif issubclass(c, SpectroscopyModel):
        model = GenericSpectroscopyModel.instantiate(c, args.happy_data_base_dir, args.target_value)
    else:
        raise Exception("Unsupported base model class: %s" % str(c))
    logger.info("Fitting model...")
    model.fit(train_ids, args.target_value)

    # get_training_data() may not exist
    if issubclass(c, ScikitSpectroscopyModel):
        csv_writer = CSVTrainingDataWriter(args.output_folder)
        csv_writer.write_data(model.get_training_data(), "training_data")

    if issubclass(c, ScikitSpectroscopyModel):
        logger.info("Predicting...")
        predictions, actuals = model.predict_images(test_ids, return_actuals=True)

        evl = RegressionEvaluator(happy_splitter, model, args.target_value)

        predictions = PredictionActualHandler.to_list(predictions,remove_last_dim=True)
        actuals = PredictionActualHandler.to_list(actuals,remove_last_dim=True)
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
