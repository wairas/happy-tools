import argparse
import os
import time
import traceback

from happy.base.core import load_class
from happy.model.generic import GenericUnsupervisedPixelClusterer
from happy.model.unsupervised_pixel_clusterer import create_false_color_image, create_prediction_image, UnsupervisedPixelClusterer
from happy.splitter.happy_splitter import HappySplitter


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate clustering on hyperspectral data using specified class from Python module.',
        prog="happy-generic-unsupervised-build",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--data_folder', type=str, help='Directory containing the HAPPy data', required=True)
    parser.add_argument('-P', '--python_file', type=str, help='The Python module with the model class to load')
    parser.add_argument('-c', '--python_class', type=str, help='The name of the model class to load')
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')

    args = parser.parse_args()
    
    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0, 0)

    # Instantiate the model
    c = load_class(args.python_file, "happy.generic_unsupervised." + str(int(round(time.time() * 1000))), args.python_class)
    if issubclass(c, UnsupervisedPixelClusterer):
        clusterer = GenericUnsupervisedPixelClusterer.instantiate(c, args.data_folder, 'target_variable_name')
    else:
        raise Exception("Unsupported base model class: %s" % str(c))

    # Fit the clusterer
    clusterer.fit(train_ids, 'target_variable_name')

    # Predict cluster labels
    predictions, actuals = clusterer.predict_images(test_ids)

    # Create grayscale and false color images for visualization
    for i, prediction in enumerate(predictions):
        prediction_image = create_prediction_image(prediction)
        prediction_image.save(os.path.join(args.output_folder, f'prediction_{i}.png'))

        false_color_image = create_false_color_image(prediction)
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
