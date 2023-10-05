import argparse
import os
import time
import traceback

import numpy as np

from happy.base.core import load_class
from happy.evaluators import PredictionActualHandler, RegressionEvaluator
from happy.model.generic import GenericSpectroscopyModel, GenericScikitSpectroscopyModel
from happy.model.spectroscopy_model import create_false_color_image, SpectroscopyModel
from happy.model.scikit_spectroscopy_model import ScikitSpectroscopyModel
from happy.splitters import HappySplitter
from happy.writers import CSVTrainingDataWriter


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified class from Python module.',
        prog="happy-generic-regression-build",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the HAPPy data')
    parser.add_argument('-P', '--python_file', type=str, help='The Python module with the model class to load')
    parser.add_argument('-c', '--python_class', type=str, help='The name of the model class to load')
    parser.add_argument('-t', '--target_value', type=str, help='Target value column name')
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file')
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions')
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 1)')

    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)

    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0, 0)

    c = load_class(args.python_file, "happy.generic_regression." + str(int(round(time.time() * 1000))), args.python_class)
    if issubclass(c, ScikitSpectroscopyModel):
        model = GenericScikitSpectroscopyModel.instantiate(c, args.happy_data_base_dir, args.target_value)
    elif issubclass(c, SpectroscopyModel):
        model = GenericSpectroscopyModel.instantiate(c, args.happy_data_base_dir, args.target_value)
    else:
        raise Exception("Unsupported base model class: %s" % str(c))
    model.fit(train_ids, args.target_value)

    # get_training_data() may not exist
    if issubclass(c, ScikitSpectroscopyModel):
        csv_writer = CSVTrainingDataWriter(args.output_folder)
        csv_writer.write_data(model.get_training_data(), "training_data")

    if issubclass(c, ScikitSpectroscopyModel):
        predictions, actuals = model.predict_images(test_ids, return_actuals=True)

        evl = RegressionEvaluator(happy_splitter, model, args.target_value)

        predictions = PredictionActualHandler.to_list(predictions,remove_last_dim=True)
        actuals = PredictionActualHandler.to_list(actuals,remove_last_dim=True)
        print(f"predictions.shape:{predictions[0].shape}  actuals.shape:{actuals[0].shape}")

        flat_actuals = np.concatenate(actuals).flatten()
        max_actual = np.nanmax(flat_actuals)
        min_actual = np.nanmin(flat_actuals)

        # Save the predictions as PNG images
        for i, prediction in enumerate(predictions):
            evl.accumulate_stats(np.array(predictions[i]), actuals[i], 0, 0)
            if np.isnan(min_actual) or np.isnan(max_actual) or (min_actual == max_actual):
                print("NaN value detected. Cannot proceed with gradient calculation.")
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
