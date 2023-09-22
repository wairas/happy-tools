# happy-tools
Python tools for dealing with hyperspectral images.

## Installation

```
pip install git+https://github.com/wairas/happy-tools.git
```

## Docker

For Docker images, please see [docker/README.md](docker/README.md).


## Command-line

### Data Viewer

```
usage: happy-data-viewer [-h] [-f BASE_FOLDER] [-d DELAY]
                         [--listbox_selectbackground LISTBOX_SELECTBACKGROUND]
                         [--listbox_selectforeground LISTBOX_SELECTFOREGROUND]

Viewer for HAPPy data folder structures.

optional arguments:
  -h, --help            show this help message and exit
  -f BASE_FOLDER, --base_folder BASE_FOLDER
                        Base folder to display (default: None)
  -d DELAY, --delay DELAY
                        The delay in msec before displaying the base folder
                        (default: 1000)
  --listbox_selectbackground LISTBOX_SELECTBACKGROUND
                        The background color to use for selected items in
                        listboxes (default: #4a6984)
  --listbox_selectforeground LISTBOX_SELECTFOREGROUND
                        The foreground color to use for selected items in
                        listboxes (default: #ffffff)
```


### ENVI Viewer

```
usage: happy-envi-viewer [-h] [-s SCAN] [-f BLACK_REFERENCE]
                         [-w WHITE_REFERENCE] [-r INT] [-g INT] [-b INT]
                         [--autodetect_channels] [--keep_aspectratio]
                         [--check_scan_dimensions]
                         [--annotation_color HEXCOLOR] [--redis_host HOST]
                         [--redis_port PORT] [--redis_pw PASSWORD]
                         [--redis_in CHANNEL] [--redis_out CHANNEL]
                         [--redis_connect] [--marker_size INT]
                         [--marker_color HEXCOLOR] [--min_obj_size INT]

ENVI Hyperspectral Image Viewer. Offers contour detection using SAM (Segment-
Anything: https://github.com/waikato-datamining/pytorch/tree/master/segment-
anything)

optional arguments:
  -h, --help            show this help message and exit
  -s SCAN, --scan SCAN  Path to the scan file (ENVI format) (default: None)
  -f BLACK_REFERENCE, --black_reference BLACK_REFERENCE
                        Path to the black reference file (ENVI format)
                        (default: None)
  -w WHITE_REFERENCE, --white_reference WHITE_REFERENCE
                        Path to the white reference file (ENVI format)
                        (default: None)
  -r INT, --scale_r INT
                        the wave length to use for the red channel (default:
                        None)
  -g INT, --scale_g INT
                        the wave length to use for the green channel (default:
                        None)
  -b INT, --scale_b INT
                        the wave length to use for the blue channel (default:
                        None)
  --autodetect_channels
                        whether to determine the channels from the meta-data
                        (overrides the manually specified channels) (default:
                        None)
  --keep_aspectratio    whether to keep the aspect ratio (default: None)
  --check_scan_dimensions
                        whether to compare the dimensions of subsequently
                        loaded scans and output a warning if they differ
                        (default: None)
  --annotation_color HEXCOLOR
                        the color to use for the annotations like contours
                        (hex color) (default: None)
  --redis_host HOST     The Redis host to connect to (IP or hostname)
                        (default: None)
  --redis_port PORT     The port the Redis server is listening on (default:
                        None)
  --redis_pw PASSWORD   The password to use with the Redis server (default:
                        None)
  --redis_in CHANNEL    The channel that SAM is receiving images on (default:
                        None)
  --redis_out CHANNEL   The channel that SAM is broadcasting the detections on
                        (default: None)
  --redis_connect       whether to immediately connect to the Redis host
                        (default: None)
  --marker_size INT     The size in pixels for the SAM points (default: None)
  --marker_color HEXCOLOR
                        the color to use for the SAM points (hex color)
                        (default: None)
  --min_obj_size INT    The minimum size that SAM contours need to have (<= 0
                        for no minimum) (default: None)
```

### Generate image regions objects

```
usage: happy-generate-image-regions-objects [-h] source_folder output_folder

Generate datasets as numpy cubes, to be loaded into deep learning datasets.

positional arguments:
  source_folder  Path to source folder containing HDR files
  output_folder  Path to output folder

optional arguments:
  -h, --help     show this help message and exit
```


### HDR Info

```
usage: happy-hdr-info [-h] hdrfile

Load and print information about an HDR file.

positional arguments:
  hdrfile     Path to the HDR file

optional arguments:
  -h, --help  show this help message and exit
```

### HSI to CSV

```
usage: happy-hsi2csv [-h] -d DIR -m DIR -s FILE -o DIR
                     [-M [METADATA_VALUES [METADATA_VALUES ...]]] -T
                     TARGETS [TARGETS ...]

Generates CSV files from hyperspectral images.

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --data_dir DIR
                        the directory with the hyperspectral data files
                        (default: None)
  -m DIR, --metadata_dir DIR
                        the directory with the meta-data JSON files (default:
                        None)
  -s FILE, --sample_ids FILE
                        the JSON file with the array of sample IDs to process
                        (default: None)
  -o DIR, --output_dir DIR
                        the directory to store the results in (default: None)
  -M [METADATA_VALUES [METADATA_VALUES ...]], --metadata_values [METADATA_VALUES [METADATA_VALUES ...]]
                        the meta-data values to add to the output (default:
                        None)
  -T TARGETS [TARGETS ...], --targets TARGETS [TARGETS ...]
                        the target values to generate data for (default: None)
```

### HSI to RGB

```
usage: happy-hsi2rgb [-h] -i INPUT_DIR [INPUT_DIR ...] [-r] [-e EXTENSION]
                     [-b BLACK_REFERENCE] [-w WHITE_REFERENCE] [-a]
                     [--red INT] [--green INT] [--blue INT] [-o OUTPUT_DIR]
                     [--width INT] [--height INT] [-n] [-v]

Fake RGB image generator for HSI files.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR [INPUT_DIR ...], --input_dir INPUT_DIR [INPUT_DIR ...]
                        Path to the scan file (ENVI format) (default: None)
  -r, --recursive       whether to traverse the directories recursively
                        (default: False)
  -e EXTENSION, --extension EXTENSION
                        The file extension to look for (default: .hdr)
  -b BLACK_REFERENCE, --black_reference BLACK_REFERENCE
                        Path to the black reference file (ENVI format)
                        (default: None)
  -w WHITE_REFERENCE, --white_reference WHITE_REFERENCE
                        Path to the white reference file (ENVI format)
                        (default: None)
  -a, --autodetect_channels
                        whether to determine the channels from the meta-data
                        (overrides the manually specified channels) (default:
                        False)
  --red INT             the wave length to use for the red channel (0-based)
                        (default: 0)
  --green INT           the wave length to use for the green channel (0-based)
                        (default: 0)
  --blue INT            the wave length to use for the blue channel (0-based)
                        (default: 0)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        The directory to store the fake RGB PNG images instead
                        of alongside the HSI images. (default: None)
  --width INT           the width to scale the images to (<= 0 uses image
                        dimension) (default: 0)
  --height INT          the height to scale the images to (<= 0 uses image
                        dimension) (default: 0)
  -n, --dry_run         whether to omit saving the PNG images (default: False)
  -v, --verbose         whether to be more verbose with the output (default:
                        False)
```


### Matlab file Info

```
usage: happy-mat-info [-h] matfile

Load and display structs from a MATLAB file.

positional arguments:
  matfile     Path to the MATLAB file

optional arguments:
  -h, --help  show this help message and exit
```


### OPEX to ENVI

```
usage: happy-opex2happy [-h] -i DIR [DIR ...] [-o DIR] -f {flat,dir-tree} -l
                        LABELS [-I] [-n] [-v]

Turns annotations (PNG and OPEX JSON) into Happy ENVI format.

optional arguments:
  -h, --help            show this help message and exit
  -i DIR [DIR ...], --input_dir DIR [DIR ...]
                        Path to the PNG/OPEX files (default: None)
  -o DIR, --output_dir DIR
                        The directory to store the fake RGB PNG images instead
                        of alongside the HSI images. (default: None)
  -f {flat,dir-tree}, --output_format {flat,dir-tree}
                        Defines how to store the data in the output directory.
                        (default: flat)
  -l LABELS, --labels LABELS
                        The comma-separated list of object labels to export
                        ('Background' is automatically added). (default: None)
  -I, --include_input   whether to copy the PNG/JSON file across to the output
                        dir (default: False)
  -n, --dry_run         whether to omit saving the PNG images (default: False)
  -v, --verbose         whether to be more verbose with the output (default:
                        False)
```


### Plot pre-processors

```
usage: happy-plot-preproc [-h] [--pixels PIXELS] foldername

Plot set of pixels with various pre-processing.

positional arguments:
  foldername       Folder containing HappyData files

optional arguments:
  -h, --help       show this help message and exit
  --pixels PIXELS  Number of random pixels to select (default: 100)
```


### Scikit Regression Build 

```
usage: happy-scikit-regression-build [-h] [--repeat_num REPEAT_NUM]
                                     happy_data_base_dir regression_method
                                     regression_params target_value
                                     happy_splitter_file output_folder

Evaluate regression model on Happy Data using specified splits and pixel
selector.

positional arguments:
  happy_data_base_dir   Directory containing the Happy Data files
  regression_method     Regression method name
  regression_params     JSON string containing regression parameters
  target_value          Target value column name
  happy_splitter_file   Happy Splitter file
  output_folder         Output JSON file to store the predictions

optional arguments:
  -h, --help            show this help message and exit
  --repeat_num REPEAT_NUM
                        Repeat number (default: 1) (default: 0)
```

### Scikit Unsupervised Build

```
usage: happy-scikit-unsupervised-build [-h] [--repeat_num REPEAT_NUM]
                                       data_folder clusterer_name
                                       clusterer_params target_value
                                       happy_splitter_file output_folder

Evaluate clustering on hyperspectral data using specified clusterer and pixel
selector.

positional arguments:
  data_folder           Directory containing the hyperspectral data
  clusterer_name        Clusterer name (e.g., kmeans, agglomerative, spectral,
                        dbscan, meanshift)
  clusterer_params      JSON string containing clusterer parameters
  target_value          Target value column name
  happy_splitter_file   Happy Splitter file
  output_folder         Output JSON file to store the predictions

optional arguments:
  -h, --help            show this help message and exit
  --repeat_num REPEAT_NUM
                        Repeat number (default: 1) (default: 0)
```

### Splitter

```
usage: happy-splitter [-h] [--num_repeats NUM_REPEATS] [--num_folds NUM_FOLDS]
                      [--train_percent TRAIN_PERCENT]
                      [--validation_percent VALIDATION_PERCENT]
                      [--use_regions] [--holdout_percent HOLDOUT_PERCENT]
                      [--output_file OUTPUT_FILE]
                      happy_base_folder

Generate train/validation/test splits for Happy data.

positional arguments:
  happy_base_folder     Path to the Happy base folder

optional arguments:
  -h, --help            show this help message and exit
  --num_repeats NUM_REPEATS
                        Number of repeats (default: 1)
  --num_folds NUM_FOLDS
                        Number of folds (default: 1)
  --train_percent TRAIN_PERCENT
                        Percentage of data in the training set (default: 70.0)
  --validation_percent VALIDATION_PERCENT
                        Percentage of data in the validation set (default:
                        10.0)
  --use_regions         Use regions in generating splits (default: False)
  --holdout_percent HOLDOUT_PERCENT
                        Percentage of data to hold out as a holdout set
                        (default: None)
  --output_file OUTPUT_FILE
                        Path to the output split file (default:
                        output_split.json)
```
