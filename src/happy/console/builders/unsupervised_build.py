import argparse
import logging
import os
import traceback

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.splitters import DataSplits
from happy.models.sklearn import create_model, CLUSTERING_MODEL_MAP
from happy.models.unsupervised_pixel_clusterer import UnsupervisedPixelClusterer, create_false_color_image, create_prediction_image
from happy.pixel_selectors import MultiSelector, PixelSelector
from happy.preprocessors import Preprocessor, MultiPreprocessor


PROG = "happy-scikit-unsupervised-build"

logger = logging.getLogger(PROG)


def default_preprocessors() -> str:
    args = [
        "wavelength-subset -f 60 -t 189",
        "snv",
        "derivative",
        "pca -n 5 -p 20",
    ]
    return " ".join(args)


def default_pixel_selectors() -> str:
    args = [
        "ps-simple -n 32 -b",
    ]
    return " ".join(args)


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Evaluate clustering on hyperspectral data using specified clusterer and pixel selector.',
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--data_folder', type=str, help='Directory containing the hyperspectral data', required=True)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data. Either preprocessor command-line(s) or file with one preprocessor command-line per line.', required=False, default=default_preprocessors())
    parser.add_argument('-S', '--pixel_selectors', type=str, help='The pixel selectors to use. Either pixel selector command-line(s) or file with one pixel selector command-line per line.', required=False, default=default_pixel_selectors())
    parser.add_argument('-m', '--clusterer_method', type=str, default="kmeans", help='Clusterer name (e.g., ' + ",".join(CLUSTERING_MODEL_MAP.keys()) + ') or full class name')
    parser.add_argument('-p', '--clusterer_params', type=str, default="{}", help='JSON string containing clusterer parameters')
    parser.add_argument('-s', '--splits_file', type=str, help='Happy Splitter file', required=True)
    parser.add_argument('-o', '--output_folder', type=str, help='Output JSON file to store the predictions', required=True)
    parser.add_argument('-r', '--repeat_num', type=int, default=0, help='Repeat number (default: 0)')
    add_logging_level(parser, short_opt="-V")

    args = parser.parse_args()
    set_logging_level(logger, args.logging_level)

    # Create the output folder if it doesn't exist
    logger.info("Creating output dir: %s" % args.output_folder)
    os.makedirs(args.output_folder, exist_ok=True)

    # splits
    logger.info("Loading splits: %s" % args.splits_file)
    splits = DataSplits.load(args.splits_file)
    train_ids, valid_ids, test_ids = splits.get_train_validation_test_splits(0, 0)

    # pixel selector
    logger.info("Creating pixel selector")
    predict_pixel_selector = MultiSelector(PixelSelector.parse_pixel_selectors(args.pixel_selectors))

    # preprocessing
    logger.info("Creating pre-processing")
    preproc = MultiPreprocessor(preprocessor_list=Preprocessor.parse_preprocessors(args.preprocessors))

    # cluster algorithm
    logger.info("Creating clusterer method: %s, options: %s" % (args.clusterer_method, str(args.clusterer_params)))
    cluster_model = create_model(args.clusterer_method, args.clusterer_params)
    # Instantiate the UnsupervisedPixelClusterer
    clusterer = UnsupervisedPixelClusterer(args.data_folder, 'target_variable_name', clusterer=cluster_model, pixel_selector=predict_pixel_selector, happy_preprocessor=preproc)

    # Fit the clusterer
    logger.info("Fitting model...")
    clusterer.fit(train_ids)

    # Predict cluster labels
    logger.info("Predicting...")
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
