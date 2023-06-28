# happy-tools
Python tools for dealing with hyper-spectral images.

## Installation

```
pip install git+https://github.com/wairas/happy-tools.git
```

## Command-line

### HSI to CSV

```
usage: happy-hsi2csv [-h] -d DIR -m DIR -s FILE -o DIR
                     [-M [METADATA_VALUES [METADATA_VALUES ...]]] -T
                     TARGETS [TARGETS ...]

Generates CSV files from hyper-spectral images.

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --data_dir DIR
                        the directory with the hyper-spectral data files
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

### ENVI Viewer

```
usage: happy-viewer [-h] [-r INT] [-g INT] [-b INT] [filename]

Display ENVI file in false color.

positional arguments:
  filename             Path to the ENVI file (default: None)

optional arguments:
  -h, --help           show this help message and exit
  -r INT, --red INT    the wave length to use for the red channel (default: 0)
  -g INT, --green INT  the wave length to use for the green channel (default:
                       0)
  -b INT, --blue INT   the wave length to use for the blue channel (default:
                       0)
```
