import argparse
import logging
import os
import traceback

import matplotlib.pyplot as plt

from wai.logging import add_logging_level, set_logging_level
from happy.base.app import init_app
from happy.pixel_selectors import PixelSelector, MultiSelector
from happy.preprocessors import Preprocessor, WavelengthSubsetPreprocessor
from happy.readers import HappyReader


PROG = "happy-plot-preproc"


logger = logging.getLogger(PROG)


def default_preprocessors() -> str:
    args = [
        "pass-through",
        "multi-pp -p 'derivative -w 15 -d 0 snv'",
        "derivative -w 15 -d 0",
        "sni",
    ]
    return " ".join(args)


def default_pixel_selectors() -> str:
    args = [
        "simple-ps -n 100 -b",
    ]
    return " ".join(args)


def main():
    init_app()
    parser = argparse.ArgumentParser(
        description="Plot set of pixels with various pre-processing setups.",
        prog=PROG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', "--input_dir", type=str, help="Folder containing HAPPy data files", required=True)
    parser.add_argument('-f', '--from_index', type=int, help='The first wavelength index to include (0-based)', required=False, default=60)
    parser.add_argument('-t', '--to_index', type=int, help='The last wavelength index to include (0-based)', required=False, default=189)
    parser.add_argument('-P', '--preprocessors', type=str, help='The preprocessors to apply to the data separately; use "multi-pp" if you need to combine multiple steps. Either preprocessor command-line(s) or file with one preprocessor command-line per line.', required=False, default=default_preprocessors())
    parser.add_argument('-S', '--pixel_selectors', type=str, help='The pixel selectors to use. Either pixel selector command-line(s) or file with one pixel selector command-line per line.', required=False, default=default_pixel_selectors())
    add_logging_level(parser, short_opt="-V")
    args = parser.parse_args()
    set_logging_level(logger, args.logging_level)

    if not os.path.exists(args.input_dir):
        raise Exception("Input dir does not exist: %s" % args.input_dir)

    parent_folder = os.path.basename(os.path.dirname(args.input_dir))
    base_folder = os.path.dirname(os.path.dirname(args.input_dir))
    sample_id = f"{parent_folder}:{os.path.basename(args.input_dir)}"
    logger.info(f"sample_id:{sample_id}, base:{base_folder}")

    # Create a HappyReader instance
    happy_reader = HappyReader(base_folder)

    # Load the HappyData for the given sample ID
    happy_data = happy_reader.load_data(sample_id)
    if len(happy_data) == 0:
        raise Exception("Failed to load data for sample ID: %s" % sample_id)

    w = WavelengthSubsetPreprocessor(from_index=args.from_index, to_index=args.to_index)
    d = happy_data[0].apply_preprocess(w)

    # List of preprocessors
    pre_processors = Preprocessor.parse_preprocessors(args.preprocessors)

    # Create a PixelSelector instance
    pixel_selector = MultiSelector(PixelSelector.parse_pixel_selectors(args.pixel_selectors))

    fig, axes = plt.subplots(nrows=len(pre_processors), figsize=(10, 6 * len(pre_processors)))

    # get a random subset of pixels
    selected_pixels = pixel_selector.select_pixels(d)
    
    # Iterate through preprocessors and corresponding subplots
    for pre_processor, ax in zip(pre_processors, axes):
        # Apply the current preprocessor to the HappyData
        preprocessed_data = d.apply_preprocess(pre_processor)

        preprocessor_params = pre_processor.to_string()
        ax.set_title(f"Pre-processor: {pre_processor.__class__.__name__} Params: {preprocessor_params}", fontsize=10)

        # Plot data for all selected pixels on the same subplot
        for x, y, _ in selected_pixels:
            pixel_value = preprocessed_data.get_spectrum(x=x, y=y)
            ax.plot(preprocessed_data.get_wavelengths(), pixel_value)

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
