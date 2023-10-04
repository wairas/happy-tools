import argparse
import os
import traceback

import numpy as np

from happy.evaluators.prediction_actual_handler import PredictionActualHandler
from happy.evaluators.regression_evaluator import RegressionEvaluator
from happy.model.scikit_spectroscopy_model import ScikitSpectroscopyModel
from happy.model.sklearn_models import create_model, REGRESSION_MODEL_MAP
from happy.model.spectroscopy_model import create_false_color_image
from happy.pixel_selectors.multi_selector import MultiSelector
from happy.pixel_selectors.simple_selector import SimpleSelector
from happy.preprocessors.preprocessor import Preprocessor
from happy.preprocessors.preprocessors import MultiPreprocessor
from happy.splitter.happy_splitter import HappySplitter
from happy.writers.csv_training_data_writer import CSVTrainingDataWriter


def default_preprocessors() -> str:
    args = [
        "wavelength-subset -f 60 -t 189",
        "sni",
        "snv",
        "derivative -w 15",
        "pad -W 128 -H 128 -v 0",
    ]
    return " ".join(args)


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified splits and pixel selector.',
        prog="happy-scikit-regression-build",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_data_base_dir', type=str, help='Directory containing the Happy Data files', required=True)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data', required=False, default=default_preprocessors())
    parser.add_argument('-m', '--regression_method', type=str, default="linearregression", help='Regression method name (e.g., ' + ",".join(REGRESSION_MODEL_MAP.keys()) + ' or full class name)')
    parser.add_argument('-p', '--regression_params', type=str, default="{}", help='JSON string containing regression parameters')
    parser.add_argument('-t', '--target_value', type=str, help='Target value column name', required=True)
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')

    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    regression_method = create_model(args.regression_method, args.regression_params)
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0,0)
    
    pixel_selector0 = SimpleSelector(64, criteria=None)
    train_pixel_selectors = MultiSelector([pixel_selector0])

    # preprocessing
    preproc = MultiPreprocessor(preprocessor_list=Preprocessor.parse_preprocessors(args.preprocessors))

    # model
    model = ScikitSpectroscopyModel(args.happy_data_base_dir, args.target_value, happy_preprocessor=preproc, additional_meta_data=None, pixel_selector=train_pixel_selectors, model=regression_method, training_data = None)
    model.fit(train_ids, force=True, keep_training_data=False)
    
    csv_writer = CSVTrainingDataWriter(args.output_folder)
    csv_writer.write_data(model.get_training_data(), "training_data")

    predictions, actuals = model.predict_images(test_ids, return_actuals=True)
    
    evl = RegressionEvaluator(happy_splitter, model, args.target_value)

    predictions = PredictionActualHandler.to_list(predictions, remove_last_dim=True)
    actuals = PredictionActualHandler.to_list(actuals,remove_last_dim=True)
    print(f"predictions.shape:{predictions[0].shape}  actuals.shape:{actuals[0].shape}")
    
    flat_actuals = np.concatenate(actuals).flatten()
    max_actual = np.nanmax(flat_actuals)
    min_actual = np.nanmin(flat_actuals)

    # Save the predictions as PNG images
    for i, prediction in enumerate(predictions):
        evl.accumulate_stats(np.array(predictions[i]),actuals[i],0,0)
        if np.isnan(min_actual) or np.isnan(max_actual) or min_actual==max_actual:
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
