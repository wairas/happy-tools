import argparse
import matplotlib.pyplot as plt
import os
import traceback
from happy.readers.happy_reader import HappyReader
from happy.pixel_selectors.simple_selector import SimpleSelector
from happy.preprocessors import SNVPreprocessor, MultiPreprocessor, DerivativePreprocessor, PassThrough, WavelengthSubsetPreprocessor, SpectralNoiseInterpolator

"""
   Use this script to display a set of pixels with various pre-processing

   e.g. python plot_pp.py Y:\happy\projects\cannabis\happy_5_v2_objects\08_NIR_MD05PID07JN01_F\1_0 --pixels 200
"""


def main():
    parser = argparse.ArgumentParser(
        description="Plot set of pixels with various pre-processing.",
        prog="happy-plot-preproc",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', "--input_dir", type=str, help="Folder containing HAPPy data files", required=True)
    parser.add_argument('-p', "--pixels", type=int, default=100, help="Number of random pixels to select")
    args = parser.parse_args()
    foldername = args.input_dir
    num_pixels = args.pixels
    
    parent_folder = os.path.basename(os.path.dirname(foldername))
    base_folder = os.path.dirname(os.path.dirname(foldername))
    sample_id = f"{parent_folder}:{os.path.basename(foldername)}"
    print(f"sample_id:{sample_id}  base:{base_folder}")

    # Create a HappyReader instance
    happy_reader = HappyReader(base_folder)

    # Load the HappyData for the given sample ID
    happy_data = happy_reader.load_data(sample_id)

    subset_indices = list(range(60, 190))
    w = WavelengthSubsetPreprocessor(subset_indices=subset_indices)  
    d = happy_data[0].apply_preprocess(w)

    # List of preprocessors
    pre_processors = [
        PassThrough(),
        MultiPreprocessor(preprocessor_list=[DerivativePreprocessor(window_length=15, deriv=0),SNVPreprocessor()]),
        DerivativePreprocessor(window_length=15, deriv=0),
        SpectralNoiseInterpolator(),
        # Add other preprocessors as needed
    ]

    # Create a PixelSelector instance
    pixel_selector = SimpleSelector(num_pixels, criteria=None, include_background=True)

    fig, axes = plt.subplots(nrows=len(pre_processors), figsize=(10, 6 * len(pre_processors)))

    # get a random subset of pixels
    selected_pixels = pixel_selector.select_pixels(d)
    
    # Iterate through preprocessors and corresponding subplots
    for pre_processor, ax in zip(pre_processors, axes):
        # Apply the current preprocessor to the HappyData
        preprocessed_data = d.apply_preprocess(pre_processor)

        preprocessor_params = pre_processor.to_string()
        ax.set_title(f"Pre_processor: {pre_processor.__class__.__name__} Params: {preprocessor_params}",fontsize=10)

        # Plot data for all selected pixels on the same subplot
        for x, y, _ in selected_pixels:
            pixel_value = preprocessed_data.get_spectrum(x=x, y=y)
            ax.plot(preprocessed_data.get_wavelengths(), pixel_value)#, label=f"Pixel: ({x}, {y})")

    # Adjust layout to avoid overlap
    plt.subplots_adjust(top=0.95, bottom=0.08, left=0.1, right=0.95, hspace=0.5)

    plt.show()


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
