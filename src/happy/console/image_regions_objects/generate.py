import os
import argparse
import traceback

from happy.data import configure_envi_settings
from happy.readers import HappyReader
from happy.writers import HappyWriter
from happy.criteria import Criteria, OP_NOT_IN
from happy.region_extractors import ObjectRegionExtractor


def process_ids(ids, reader, region_extractor, output_dir):
    writer = HappyWriter(output_dir)

    for sample_id in ids:
        print(sample_id)
        # Load data
        happy_data_list = reader.load_data(sample_id)
        # print(happy_data_list)
        for happy_data in happy_data_list:
            # Get regions and save them
            region_list = region_extractor.extract_regions(happy_data)

            for region_happy_data in region_list:
                writer.write_data(region_happy_data)


def get_sample_ids(source_folder):
    ids = [name for name in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, name))]
    return ids


def main():
    configure_envi_settings()
    parser = argparse.ArgumentParser(
        description='Generate datasets as numpy cubes, to be loaded into deep learning datasets.',
        prog="happy-generate-image-regions-objects",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_dir', type=str, help='Path to source folder containing HDR files', required=True)
    parser.add_argument('-o', '--output_dir', type=str, help='Path to output folder', required=True)
    args = parser.parse_args()

    # Load sample IDs using the get_sample_ids method
    ids = get_sample_ids(args.input_dir)

    # Initialize the spectra reader object for reading .mat files
    happy_reader = HappyReader(args.input_dir)

    object_key = "object"
    not_background_criteria = Criteria(OP_NOT_IN, key=object_key, value=[0, "0"])
    # Initialize the region extractor object
    # Use SimpleRegionExtractor to get the whole image
    region_extractor = ObjectRegionExtractor(object_key, target_name=None, base_criteria=[not_background_criteria])

    # Process the IDs and save the regions

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Folder '{args.output_dir}' created successfully!")
    else:
        print(f"Folder '{args.output_dir}' already exists.")
    process_ids(ids, happy_reader, region_extractor, args.output_dir)


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
