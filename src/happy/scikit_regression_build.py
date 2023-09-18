from PIL import Image

import os
import numpy as np
import traceback

import argparse
from happy.splitter.happy_splitter import HappySplitter
from happy.model.scikit_spectroscopy_model import ScikitSpectroscopyModel
from happy.writers.csv_training_data_writer import CSVTrainingDataWriter

from happy.pixel_selectors.simple_selector import SimpleSelector
from happy.pixel_selectors.multi_selector import MultiSelector
from happy.evaluators.regression_evaluator import RegressionEvaluator
from happy.evaluators.prediction_actual_handler import PredictionActualHandler
from happy.preprocessors.preprocessors import SpectralNoiseInterpolator, PadPreprocessor, SNVPreprocessor, MultiPreprocessor, DerivativePreprocessor, WavelengthSubsetPreprocessor


def create_false_color_image(predictions, min_actual, max_actual):
    # Find the minimum and maximum values of actuals
    predictions = predictions[:, :]

    # Create an empty array for the false color image
    false_color = np.zeros((predictions.shape[0], predictions.shape[1], 4), dtype=np.uint8)

    max_actual = max_actual * 1.15
    for i in range(predictions.shape[0]):
        for j in range(predictions.shape[1]):
            prediction = predictions[i, j]

            if prediction <= 0:
                # Zero value is transparent
                # color = [0, 0, 0, 0]
                color = [0, 0, 255, 255]
            elif prediction < min_actual:
                # Values below the minimum are blue
                color = [0, 0, 255, 255]
            elif prediction > max_actual:
                # Values above the maximum are red
                color = [255, 0, 0, 255]
            else:
                # Calculate the gradient color based on the range of actual values
                gradient = (prediction - min_actual) / (max_actual - min_actual)
                r = int(255 * (1 - gradient))
                g = int(255 * (1 - gradient))
                b = int(128 * gradient)
                color = [r, g, b, 255]

            # Assign the color to the false color image
            false_color[i, j] = color

    false_color_image = Image.fromarray(false_color)
    return false_color_image


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate regression model on Happy Data using specified splits and pixel selector.',
        prog="happy-scikit-regr-build",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('happy_data_base_dir', type=str, help='Directory containing the Happy Data files')
    parser.add_argument('regression_method', type=str, help='Regression method name')
    parser.add_argument('regression_params', type=str, help='JSON string containing regression parameters')
    parser.add_argument('target_value', type=str, help='Target value column name')
    parser.add_argument('happy_splitter_file', type=str, help='Happy Splitter file')
    parser.add_argument('output_folder', type=str, help='Output JSON file to store the predictions')
    parser.add_argument('--repeat_num', type=int, default=0, help='Repeat number (default: 1)')

    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    classification_method = ScikitSpectroscopyModel.create_model(args.regression_method, args.regression_params)
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0,0)
    
    pixel_selector0 = SimpleSelector(64, criteria=None)
    train_pixel_selectors = MultiSelector([pixel_selector0])

    subset_indices = list(range(60, 190))
    w = WavelengthSubsetPreprocessor(subset_indices=subset_indices)

    clean = SpectralNoiseInterpolator()
    SNVpp = SNVPreprocessor()
    SGpp = DerivativePreprocessor(window_length=15)
    padp = PadPreprocessor(width=128, height=128, pad_value=0)
    pp = MultiPreprocessor(preprocessor_list=[w, clean, SNVpp, SGpp, padp])
    
    model = ScikitSpectroscopyModel(args.happy_data_base_dir, args.target_value, happy_preprocessor=pp, additional_meta_data=None, pixel_selector=train_pixel_selectors, model=classification_method, training_data = None)
    model.fit(train_ids, force=True, keep_training_data=False)
    
    csv_writer = CSVTrainingDataWriter(args.output_folder)
    csv_writer.write_data(model.get_training_data(), "training_data")

    predictions, actuals = model.predict_images(test_ids, return_actuals=True)
    
    eval = RegressionEvaluator(happy_splitter, model, args.target_value)

    predictions = PredictionActualHandler.to_list(predictions,remove_last_dim=True)
    actuals = PredictionActualHandler.to_list(actuals,remove_last_dim=True)
    print(f"predictions.shape:{predictions[0].shape}  actuals.shape:{actuals[0].shape}")
    
    flat_actuals = np.concatenate(actuals).flatten()
    max_actual = np.nanmax(flat_actuals)
    min_actual = np.nanmin(flat_actuals)

    # Save the predictions as PNG images
    for i, prediction in enumerate(predictions):
        eval.accumulate_stats(np.array(predictions[i]),actuals[i],0,0)
        if np.isnan(min_actual) or np.isnan(max_actual) or min_actual==max_actual:
            print("NaN value detected. Cannot proceed with gradient calculation.")
            continue
        false_color_image = create_false_color_image(prediction, min_actual, max_actual)
        false_color_image.save(os.path.join(args.output_folder, f'false_color_{i}.png'))
    eval.calculate_and_show_metrics()


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

