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
usage: happy-data-viewer [-h] [--base_folder BASE_FOLDER] [--sample SAMPLE]
                         [--repeat REPEAT] [-r INT] [-g INT] [-b INT] [-o INT]
                         [--listbox_selectbackground LISTBOX_SELECTBACKGROUND]
                         [--listbox_selectforeground LISTBOX_SELECTFOREGROUND]
                         [--log_timestamp_format FORMAT]

Viewer for HAPPy data folder structures.

optional arguments:
  -h, --help            show this help message and exit
  --base_folder BASE_FOLDER
                        Base folder to display (default: None)
  --sample SAMPLE       The sample to load (default: None)
  --repeat REPEAT       The repeat to load (default: None)
  -r INT, --scale_r INT
                        the wave length to use for the red channel (default:
                        None)
  -g INT, --scale_g INT
                        the wave length to use for the green channel (default:
                        None)
  -b INT, --scale_b INT
                        the wave length to use for the blue channel (default:
                        None)
  -o INT, --opacity INT
                        the opacity to use (0-100) (default: None)
  --listbox_selectbackground LISTBOX_SELECTBACKGROUND
                        The background color to use for selected items in
                        listboxes (default: #4a6984)
  --listbox_selectforeground LISTBOX_SELECTFOREGROUND
                        The foreground color to use for selected items in
                        listboxes (default: #ffffff)
  --log_timestamp_format FORMAT
                        the format string for the logging timestamp, see: http
                        s://docs.python.org/3/library/datetime.html#strftime-
                        and-strptime-format-codes (default: [%H:%M:%S.%f])
```


### ENVI Viewer

```
usage: happy-envi-viewer [-h] [-s SCAN] [-f BLACK_REFERENCE]
                         [-w WHITE_REFERENCE] [-r INT] [-g INT] [-b INT]
                         [--autodetect_channels] [--keep_aspectratio]
                         [--check_scan_dimensions] [--export_to_scan_dir]
                         [--annotation_color HEXCOLOR] [--redis_host HOST]
                         [--redis_port PORT] [--redis_pw PASSWORD]
                         [--redis_in CHANNEL] [--redis_out CHANNEL]
                         [--redis_connect] [--marker_size INT]
                         [--marker_color HEXCOLOR] [--min_obj_size INT]
                         [--black_ref_locator LOCATOR]
                         [--black_ref_method METHOD]
                         [--white_ref_locator LOCATOR]
                         [--white_ref_method METHOD]
                         [--preprocessing PIPELINE]
                         [--log_timestamp_format FORMAT]

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
  --export_to_scan_dir  whether to export images to the scan directory rather
                        than the last one used (default: None)
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
  --black_ref_locator LOCATOR
                        the reference locator scheme to use for locating black
                        references, eg rl-manual (default: None)
  --black_ref_method METHOD
                        the black reference method to use for applying black
                        references, eg br-same-size (default: None)
  --white_ref_locator LOCATOR
                        the reference locator scheme to use for locating
                        whites references, eg rl-manual (default: None)
  --white_ref_method METHOD
                        the white reference method to use for applying white
                        references, eg wr-same-size (default: None)
  --preprocessing PIPELINE
                        the preprocessors to apply to the scan (default: None)
  --log_timestamp_format FORMAT
                        the format string for the logging timestamp, see: http
                        s://docs.python.org/3/library/datetime.html#strftime-
                        and-strptime-format-codes (default: [%H:%M:%S.%f])
```

### Generate image regions objects

```
usage: happy-generate-image-regions-objects [-h] -i INPUT_DIR -o OUTPUT_DIR

Generate datasets as numpy cubes, to be loaded into deep learning datasets.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input_dir INPUT_DIR
                        Path to source folder containing HDR files (default:
                        None)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to output folder (default: None)
```


### HDR Info

```
usage: happy-hdr-info [-h] -i INPUT_FILE [-f] [-o OUTPUT_FILE]

Load and print information about an HDR file.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        Path to the HDR file (default: None)
  -f, --full            Whether to output all fields (default: False)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path to output file; prints to stdout if omitted
                        (default: None)
```

### HSI to RGB

```
usage: happy-hsi2rgb [-h] -i INPUT_DIR [INPUT_DIR ...] [-r] [-e EXTENSION]
                     [--black_ref_locator LOCATOR] [--black_ref_method METHOD]
                     [--white_ref_locator LOCATOR] [--white_ref_method METHOD]
                     [-a] [--red INT] [--green INT] [--blue INT]
                     [-o OUTPUT_DIR] [--width INT] [--height INT] [-n]
                     [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Fake RGB image generator for HSI files.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR [INPUT_DIR ...], --input_dir INPUT_DIR [INPUT_DIR ...]
                        Path to the scan file (ENVI format) (default: None)
  -r, --recursive       whether to traverse the directories recursively
                        (default: False)
  -e EXTENSION, --extension EXTENSION
                        The file extension to look for (default: .hdr)
  --black_ref_locator LOCATOR
                        the reference locator scheme to use for locating black
                        references, eg rl-manual (default: None)
  --black_ref_method METHOD
                        the black reference method to use for applying black
                        references, eg br-same-size (default: None)
  --white_ref_locator LOCATOR
                        the reference locator scheme to use for locating
                        whites references, eg rl-manual (default: None)
  --white_ref_method METHOD
                        the white reference method to use for applying white
                        references, eg wr-same-size (default: None)
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
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
```


### Matlab file Info

```
usage: happy-mat-info [-h] -i INPUT_FILE [-o OUTPUT_FILE]

Load and display structs from a MATLAB file.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        Path to the MATLAB file (default: None)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path to the output file; outputs to stdout if omitted
                        (default: None)
```


### OPEX to HAPPy

```
usage: happy-opex2happy [-h] -i DIR [DIR ...] [-r] [-o DIR] -f
                        {flat,dir-tree,dir-tree-with-data} -l LABELS [-N]
                        [-u UNLABELLED] [--black_ref_locator LOCATOR]
                        [--black_ref_method METHOD]
                        [--white_ref_locator LOCATOR]
                        [--white_ref_method METHOD] [--pattern_mask PATTERN]
                        [--pattern_labels PATTERN] [--pattern_png PATTERN]
                        [--pattern_annotations PATTERN] [-I] [-n] [-v]

Turns annotations (PNG and OPEX JSON) into Happy ENVI format.

optional arguments:
  -h, --help            show this help message and exit
  -i DIR [DIR ...], --input_dir DIR [DIR ...]
                        Path to the PNG/OPEX files (default: None)
  -r, --recursive       whether to look for OPEX files recursively (default:
                        False)
  -o DIR, --output_dir DIR
                        The directory to store the fake RGB PNG images instead
                        of alongside the HSI images. (default: None)
  -f {flat,dir-tree,dir-tree-with-data}, --output_format {flat,dir-tree,dir-tree-with-data}
                        Defines how to store the data in the output directory.
                        (default: dir-tree-with-data)
  -l LABELS, --labels LABELS
                        The comma-separated list of object labels to export
                        ('Background' is automatically added). (default: None)
  -N, --no_implicit_background
                        whether to require explicit annotations for the
                        background rather than assuming all un-annotated
                        pixels are background (default: False)
  -u UNLABELLED, --unlabelled UNLABELLED
                        The value to use for pixels that do not have an
                        explicit annotation (label values start after this
                        value) (default: 0)
  --black_ref_locator LOCATOR
                        the reference locator scheme to use for locating black
                        references, eg rl-manual; requires: dir-tree-with-data
                        (default: None)
  --black_ref_method METHOD
                        the black reference method to use for applying black
                        references, eg br-same-size; requires: dir-tree-with-
                        data (default: None)
  --white_ref_locator LOCATOR
                        the reference locator scheme to use for locating
                        whites references, eg rl-manual; requires: dir-tree-
                        with-data (default: None)
  --white_ref_method METHOD
                        the white reference method to use for applying white
                        references, eg wr-same-size; requires: dir-tree-with-
                        data (default: None)
  --pattern_mask PATTERN
                        the pattern to use for saving the mask ENVI file,
                        available placeholders: {SAMPLEID} (default: mask.hdr)
  --pattern_labels PATTERN
                        the pattern to use for saving the label map for the
                        mask ENVI file, available placeholders: {SAMPLEID}
                        (default: mask.json)
  --pattern_png PATTERN
                        the pattern to use for saving the mask PNG file,
                        available placeholders: {SAMPLEID} (default:
                        {SAMPLEID}.png)
  --pattern_annotations PATTERN
                        the pattern to use for saving the OPEX JSON annotation
                        file, available placeholders: {SAMPLEID} (default:
                        {SAMPLEID}.json)
  -I, --include_input   whether to copy the PNG/JSON file across to the output
                        dir (default: False)
  -n, --dry_run         whether to omit generating any data or creating
                        directories (default: False)
  -v, --verbose         whether to be more verbose with the output (default:
                        False)
```


### Plot pre-processors

```
usage: happy-plot-preproc [-h] -i INPUT_DIR [-f FROM_INDEX] [-t TO_INDEX]
                          [-P PREPROCESSORS] [-S PIXEL_SELECTORS]

Plot set of pixels with various pre-processing setups.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input_dir INPUT_DIR
                        Folder containing HAPPy data files (default: None)
  -f FROM_INDEX, --from_index FROM_INDEX
                        The first wavelength index to include (0-based)
                        (default: 60)
  -t TO_INDEX, --to_index TO_INDEX
                        The last wavelength index to include (0-based)
                        (default: 189)
  -P PREPROCESSORS, --preprocessors PREPROCESSORS
                        The preprocessors to apply to the data separately; use
                        "multi-pp" if you need to combine multiple steps
                        (default: pass-through multi-pp -p 'derivative -w 15
                        -d 0 snv' derivative -w 15 -d 0 sni)
  -S PIXEL_SELECTORS, --pixel_selectors PIXEL_SELECTORS
                        The pixel selectors to use. (default: simple-ps -n 100
                        -b)
```


### Process data

```
usage: happy-process-data reader [preprocessor(s)] writer [-h|--help|--help-all|--help-plugin NAME] 
       [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Processes data using the specified pipeline.

readers: happy-reader
preprocessors: crop, derivative, down-sample, multi-pp, pca, pad, pass-through, snv, sni, std-scaler, wavelength-subset
writers: happy-writer, matlab-writer

optional arguments:
  -h, --help            show this help message and exit
  --help-all            show the help for all plugins and exit
  --help-plugin NAME    show the help for plugin NAME and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
```


### Scikit Regression Build 

```
usage: happy-scikit-regression-build [-h] -d HAPPY_DATA_BASE_DIR
                                     [-P PREPROCESSORS] [-S PIXEL_SELECTORS]
                                     [-m REGRESSION_METHOD]
                                     [-p REGRESSION_PARAMS] -t TARGET_VALUE -s
                                     HAPPY_SPLITTER_FILE -o OUTPUT_FOLDER
                                     [-r REPEAT_NUM]

Evaluate regression model on Happy Data using specified splits and pixel
selector.

optional arguments:
  -h, --help            show this help message and exit
  -d HAPPY_DATA_BASE_DIR, --happy_data_base_dir HAPPY_DATA_BASE_DIR
                        Directory containing the Happy Data files (default:
                        None)
  -P PREPROCESSORS, --preprocessors PREPROCESSORS
                        The preprocessors to apply to the data. Either
                        preprocessor command-line(s) or file with one
                        preprocessor command-line per line. (default:
                        wavelength-subset -f 60 -t 189 sni snv derivative -w
                        15 pad -W 128 -H 128 -v 0)
  -S PIXEL_SELECTORS, --pixel_selectors PIXEL_SELECTORS
                        The pixel selectors to use. Either pixel selector
                        command-line(s) or file with one pixel selector
                        command-line per line. (default: simple-ps -n 64)
  -m REGRESSION_METHOD, --regression_method REGRESSION_METHOD
                        Regression method name (e.g., linearregression,ridge,l
                        ars,plsregression,plsneighbourregression,lasso,elastic
                        net,decisiontreeregressor,randomforestregressor,svr or
                        full class name) (default: linearregression)
  -p REGRESSION_PARAMS, --regression_params REGRESSION_PARAMS
                        JSON string containing regression parameters (default:
                        {})
  -t TARGET_VALUE, --target_value TARGET_VALUE
                        Target value column name (default: None)
  -s HAPPY_SPLITTER_FILE, --happy_splitter_file HAPPY_SPLITTER_FILE
                        Happy Splitter file (default: None)
  -o OUTPUT_FOLDER, --output_folder OUTPUT_FOLDER
                        Output JSON file to store the predictions (default:
                        None)
  -r REPEAT_NUM, --repeat_num REPEAT_NUM
                        Repeat number (default: 0) (default: 0)
```

### Scikit Unsupervised Build

```
usage: happy-scikit-unsupervised-build [-h] -d DATA_FOLDER [-P PREPROCESSORS]
                                       [-S PIXEL_SELECTORS]
                                       [-m CLUSTERER_METHOD]
                                       [-p CLUSTERER_PARAMS] -s
                                       HAPPY_SPLITTER_FILE -o OUTPUT_FOLDER
                                       [-r REPEAT_NUM]

Evaluate clustering on hyperspectral data using specified clusterer and pixel
selector.

optional arguments:
  -h, --help            show this help message and exit
  -d DATA_FOLDER, --data_folder DATA_FOLDER
                        Directory containing the hyperspectral data (default:
                        None)
  -P PREPROCESSORS, --preprocessors PREPROCESSORS
                        The preprocessors to apply to the data. Either
                        preprocessor command-line(s) or file with one
                        preprocessor command-line per line. (default:
                        wavelength-subset -f 60 -t 189 snv derivative pca -n 5
                        -p 20)
  -S PIXEL_SELECTORS, --pixel_selectors PIXEL_SELECTORS
                        The pixel selectors to use. Either pixel selector
                        command-line(s) or file with one pixel selector
                        command-line per line. (default: simple-ps -n 32 -b)
  -m CLUSTERER_METHOD, --clusterer_method CLUSTERER_METHOD
                        Clusterer name (e.g.,
                        kmeans,agglomerative,spectral,dbscan,meanshift) or
                        full class name (default: kmeans)
  -p CLUSTERER_PARAMS, --clusterer_params CLUSTERER_PARAMS
                        JSON string containing clusterer parameters (default:
                        {})
  -s HAPPY_SPLITTER_FILE, --happy_splitter_file HAPPY_SPLITTER_FILE
                        Happy Splitter file (default: None)
  -o OUTPUT_FOLDER, --output_folder OUTPUT_FOLDER
                        Output JSON file to store the predictions (default:
                        None)
  -r REPEAT_NUM, --repeat_num REPEAT_NUM
                        Repeat number (default: 0) (default: 0)
```

### Splitter

```
usage: happy-splitter [-h] -d HAPPY_BASE_FOLDER [-r NUM_REPEATS]
                      [-f NUM_FOLDS] [-t TRAIN_PERCENT]
                      [-v VALIDATION_PERCENT] [-R] [-H HOLDOUT_PERCENT] -o
                      OUTPUT_FILE

Generate train/validation/test splits for Happy data.

optional arguments:
  -h, --help            show this help message and exit
  -d HAPPY_BASE_FOLDER, --happy_base_folder HAPPY_BASE_FOLDER
                        Path to the Happy base folder (default: None)
  -r NUM_REPEATS, --num_repeats NUM_REPEATS
                        Number of repeats (default: 1)
  -f NUM_FOLDS, --num_folds NUM_FOLDS
                        Number of folds (default: 1)
  -t TRAIN_PERCENT, --train_percent TRAIN_PERCENT
                        Percentage of data in the training set (default: 70.0)
  -v VALIDATION_PERCENT, --validation_percent VALIDATION_PERCENT
                        Percentage of data in the validation set (default:
                        10.0)
  -R, --use_regions     Use regions in generating splits (default: False)
  -H HOLDOUT_PERCENT, --holdout_percent HOLDOUT_PERCENT
                        Percentage of data to hold out as a holdout set
                        (default: None)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path to the output split file (default:
                        output_split.json)
```

## Plugins

See [here](plugins/README.md) for a list of plugins and their documentation.
