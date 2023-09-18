import os
import argparse
from readers.happy_reader import HappyReader
from writers.happy_writer import HappyWriter
from criteria.criteria import Criteria
from region_extractors.object_region_extractor import ObjectRegionExtractor 

parser = argparse.ArgumentParser(description='Generate datasets as numpy cubes, to be loaded into deep learning datasets.')
parser.add_argument('source_folder', type=str, help='Path to source folder containing HDR files')
parser.add_argument('output_folder', type=str, help='Path to output folder')
args = parser.parse_args()


def process_ids(ids, reader, region_extractor, output_dir):
    writer = HappyWriter(output_dir)

    for sample_id in ids:
        print(sample_id)
        # Load data
        happy_data_list = reader.load_data(sample_id)
        #print(happy_data_list)
        for happy_data in happy_data_list:
            # Get regions and save them
            region_list = region_extractor.extract_regions(happy_data)
            
            for region_happy_data in region_list:
                
                writer.write_data(region_happy_data)
                
        
def get_sample_ids(source_folder):
    ids = [name for name in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, name))]
    return ids
   
# Load sample IDs using the get_sample_ids method
ids = get_sample_ids(args.source_folder)

# Initialize the spectra reader object for reading .mat files
happy_reader = HappyReader(args.source_folder)
    
object_key = "object"
not_background_criteria = Criteria("not_in", key=object_key, value=[0,"0"])
# Initialize the region extractor object
# Use SimpleRegionExtractor to get the whole image
region_extractor = ObjectRegionExtractor(object_key, target_name=None, base_criteria=[not_background_criteria])
#region_extractor = MaskRegionExtractor(mat_reader,'..\FinalMask',[2,3,4],['bnf_wk8'])

# Or use JsonRegionExtractor to get regions based on a JSON file
#region_extractor = JsonRegionExtractor(mat_reader, 'regions.json')

# Process the IDs and save the regions

if not os.path.exists(args.output_folder):
    os.makedirs(args.output_folder)
    print(f"Folder '{args.output_folder}' created successfully!")
else:
    print(f"Folder '{args.output_folder}' already exists.")
#output_dir = '../output/output_regions_bymask'
process_ids(ids, happy_reader, region_extractor, args.output_folder)  
