# envi-writer

Exports the data in ENVI format and the meta-data as JSON alongside.

```
usage: envi-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [-A LOGGER_NAME] [-b BASE_DIR] [-o OUTPUT]

Exports the data in ENVI format and the meta-data as JSON alongside.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: .)
  -o OUTPUT, --output OUTPUT
                        The pattern for the output files; The following
                        placeholders are available for the output pattern:
                        {BASEDIR}, {SAMPLEID}, {REPEAT}, {REGION} (default:
                        {BASEDIR}/{SAMPLEID}.{REPEAT}.hdr)
```
