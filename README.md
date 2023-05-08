# happy-hsi-to-csv
Turns hyper-spectral data into CSV files.

## Command-line

```
usage: h2c-generate-csv [-h] -d DIR -m DIR -s FILE -o DIR
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
