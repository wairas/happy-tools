# wr-annotation-avg

White reference method that computes the average per band in the annotation rectangle. Does not require scan and reference to have the same size.

```
usage: wr-annotation-avg [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                         [-A LOGGER_NAME] [-f REFERENCE_FILE]
                         [-a COORD COORD COORD COORD]

White reference method that computes the average per band in the annotation
rectangle. Does not require scan and reference to have the same size.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f REFERENCE_FILE, --reference_file REFERENCE_FILE
                        The ENVI reference file to load (default: None)
  -a COORD COORD COORD COORD, --annotation COORD COORD COORD COORD
                        The annotation rectangle (top, left, bottom, right)
                        (default: None)
```
