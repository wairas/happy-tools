# envi-reader

Reads data in ENVI format.

```
usage: envi-reader [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [-A LOGGER_NAME] [-b BASE_DIR] [-e EXT]
                   [--exclude [REGEXP [REGEXP ...]]]

Reads data in ENVI format.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: .)
  -e EXT, --extension EXT
                        The file extension to look for (incl dot), e.g.,
                        '.hdr'. (default: .hdr)
  --exclude [REGEXP [REGEXP ...]]
                        The optional regular expression(s) for excluding ENVI
                        files to read (gets applied to file name, not path).
                        (default: None)
```
