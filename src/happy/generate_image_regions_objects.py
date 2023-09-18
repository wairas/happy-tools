import os
import argparse
import traceback
from happy.readers.happy_reader import HappyReader
from happy.writers.happy_writer import HappyWriter
from happy.criteria.criteria import Criteria
from happy.region_extractors.object_region_extractor import ObjectRegionExtractor


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
    parser = argparse.ArgumentParser(
        description='Generate datasets as numpy cubes, to be loaded into deep learning datasets.',
        prog="happy-generate-image-regions-objects",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('source_folder', type=str, help='Path to source folder containing HDR files')
    parser.add_argument('output_folder', type=str, help='Path to output folder')
    args = parser.parse_args()

    # Load sample IDs using the get_sample_ids method
    ids = get_sample_ids(args.source_folder)

    # Initialize the spectra reader object for reading .mat files
    happy_reader = HappyReader(args.source_folder)

    object_key = "object"
    not_background_criteria = Criteria("not_in", key=object_key, value=[0,"0"])
    # Initialize the region extractor object
    # Use SimpleRegionExtractor to get the whole image
    region_extractor = ObjectRegionExtractor(object_key, target_name=None, base_criteria=[not_background_criteria])

    # Or use JsonRegionExtractor to get regions based on a JSON file
    #region_extractor = JsonRegionExtractor(mat_reader, 'regions.json')

    # Process the IDs and save the regions

    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
        print(f"Folder '{args.output_folder}' created successfully!")
    else:
        print(f"Folder '{args.output_folder}' already exists.")
    process_ids(ids, happy_reader, region_extractor, args.output_folder)


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
