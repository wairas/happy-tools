from PIL import Image
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from happy.splitter.happy_splitter import HappySplitter
from happy.model.unsupervised_pixel_clusterer import UnsupervisedPixelClusterer
from happy.pixel_selectors.simple_selector import SimpleSelector
from happy.pixel_selectors.multi_selector import MultiSelector
from happy.criteria.criteria import Criteria
from happy.preprocessors.preprocessors import PCAPreprocessor, SNVPreprocessor, MultiPreprocessor, DerivativePreprocessor, WavelengthSubsetPreprocessor


def main():
    parser = argparse.ArgumentParser(description='Evaluate clustering on hyperspectral data using specified clusterer and pixel selector.')
    parser.add_argument('data_folder', type=str, help='Directory containing the hyperspectral data')
    parser.add_argument('clusterer_name', type=str, help='Clusterer name (e.g., kmeans, agglomerative, spectral, dbscan, meanshift)')
    parser.add_argument('clusterer_params', type=str, help='JSON string containing clusterer parameters')
    parser.add_argument('target_value', type=str, help='Target value column name')
    parser.add_argument('happy_splitter_file', type=str, help='Happy Splitter file')
    parser.add_argument('output_folder', type=str, help='Output JSON file to store the predictions')
    parser.add_argument('--repeat_num', type=int, default=0, help='Repeat number (default: 1)')

    args = parser.parse_args()
    
    # Create the output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    happy_splitter = HappySplitter.load_splits_from_json(args.happy_splitter_file)
    train_ids, valid_ids, test_ids = happy_splitter.get_train_validation_test_splits(0,0)
    
    crit0 = Criteria("in", key="mask", value=[0])
    pixel_selector0 = SimpleSelector(32, criteria=crit0, include_background=True)
    
    crit1 = Criteria("in", key="mask", value=[1])
    pixel_selector1 = SimpleSelector(32, criteria=crit1)
    
    crit2 = Criteria("in", key="mask", value=[2])
    pixel_selector2 = SimpleSelector(32, criteria=crit2)
    
    crit3 = Criteria("in", key="mask", value=[3])
    pixel_selector3 = SimpleSelector(32, criteria=crit3)
    
    train_pixel_selectors = MultiSelector([pixel_selector0, pixel_selector1, pixel_selector2, pixel_selector3])
    predict_pixel_selector = SimpleSelector(32, criteria=None, include_background=True)
    subset_indices = list(range(60, 190))
    w = WavelengthSubsetPreprocessor(subset_indices=subset_indices)

    SNVpp = SNVPreprocessor()
    SGpp = DerivativePreprocessor()
    PCApp = PCAPreprocessor(components=5, percent_pixels=20)
    pp = MultiPreprocessor(preprocessor_list=[w, SNVpp, SGpp, PCApp])
    # Instantiate the UnsupervisedPixelClusterer
    clusterer = UnsupervisedPixelClusterer(args.data_folder, 'target_variable_name', args.clusterer_name, args.clusterer_params, pixel_selector=predict_pixel_selector, happy_preprocessor=pp )

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


def create_prediction_image(prediction):
    # Create a grayscale prediction image
    prediction_image = Image.fromarray((prediction * 255).astype(np.uint8))
    return prediction_image


def create_false_color_image(prediction):
    # Create a false color prediction image
    cmap = plt.get_cmap('viridis', np.max(prediction) + 1)
    false_color = cmap(prediction)
    false_color_image = Image.fromarray((false_color[:, :, :3] * 255).astype(np.uint8))
    return false_color_image


if __name__ == "__main__":
    main()

