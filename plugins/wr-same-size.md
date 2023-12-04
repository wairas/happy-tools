# wr-same-size

White reference method that simply divides the scan by the white reference. Requires scan and reference to have the same size.

```
usage: wr-same-size [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [-A LOGGER_NAME] [-f REFERENCE_FILE]

White reference method that simply divides the scan by the white reference.
Requires scan and reference to have the same size.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f REFERENCE_FILE, --reference_file REFERENCE_FILE
                        The ENVI reference file to load (default: None)
```
