import argparse
import os
import traceback
from happy.splitter.happy_splitter import HappySplitter
from happy.model.sklearn_models import create_model, CLUSTERING_MODEL_MAP
from happy.model.unsupervised_pixel_clusterer import UnsupervisedPixelClusterer, create_false_color_image, create_prediction_image
from happy.pixel_selectors.simple_selector import SimpleSelector
from happy.preprocessors.preprocessors import PCAPreprocessor, SNVPreprocessor, MultiPreprocessor, DerivativePreprocessor, WavelengthSubsetPreprocessor


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate clustering on hyperspectral data using specified clusterer and pixel selector.',
        prog="happy-scikit-unsupervised-build",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--data_folder', type=str, help='Directory containing the hyperspectral data', required=True)
    parser.add_argument('-m', '--clusterer_method', type=str, default="kmeans", help='Clusterer name (e.g., ' + ",".join(CLUSTERING_MODEL_MAP.keys()) + ') or full class name')
    parser.add_argument('-p', '--clusterer_params', type=str, default="{}", help='JSON string containing clusterer parameters')
    parser.add_argument('-s', '--happy_splitter_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')

    args = parser.parse_args()
    
    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0,0)

    predict_pixel_selector = SimpleSelector(32, criteria=None, include_background=True)

    # preprocessing
    subset_indices = list(range(60, 190))
    w = WavelengthSubsetPreprocessor(subset_indices=subset_indices)
    SNVpp = SNVPreprocessor()
    SGpp = DerivativePreprocessor()
    PCApp = PCAPreprocessor(components=5, percent_pixels=20)
    pp = MultiPreprocessor(preprocessor_list=[w, SNVpp, SGpp, PCApp])
    # cluster algorithm
    cluster_model = create_model(args.clusterer_method, args.clusterer_params)
    # Instantiate the UnsupervisedPixelClusterer
    clusterer = UnsupervisedPixelClusterer(args.data_folder, 'target_variable_name', cluster_model, pixel_selector=predict_pixel_selector, happy_preprocessor=pp)

    # Fit the clusterer
    clusterer.fit(train_ids)

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
