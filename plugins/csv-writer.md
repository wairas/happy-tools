# csv-writer

Generates CSV spreadsheets with spectra from the data. When omitting the repeat/region pattern from the output pattern, the CSV files get combined and meta-data output is automatically suppressed.

```
usage: csv-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-A LOGGER_NAME] -b BASE_DIR [-o OUTPUT]
                  [-w WAVE_NUMBER_PREFIX] [-i] [--suppress_metadata]

Generates CSV spreadsheets with spectra from the data. When omitting the
repeat/region pattern from the output pattern, the CSV files get combined and
meta-data output is automatically suppressed.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: None)
  -o OUTPUT, --output OUTPUT
                        The pattern for the output files; combines the
                        repeats/regions if {REPEAT} not present in output
                        pattern; The following placeholders are available for
                        the output pattern: {BASEDIR}, {SAMPLEID}, {REPEAT},
                        {REGION} (default: {BASEDIR}/{SAMPLEID}.{REPEAT}.csv)
  -w WAVE_NUMBER_PREFIX, --wave_number_prefix WAVE_NUMBER_PREFIX
                        The prefix to use for the spectral columns (default:
                        wave-)
  -i, --output_wave_number_index
                        Whether to output the index of the wave number instead
                        of the wave length (default: False)
  --suppress_metadata   Whether to suppress the output of the meta-data
                        (default: False)
```
