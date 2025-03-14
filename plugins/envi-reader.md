# envi-reader

Reads data in ENVI format.

```
usage: envi-reader [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [-A LOGGER_NAME] [-b BASE_DIR] [-e EXT]
                   [--exclude [REGEXP ...]]

Reads data in ENVI format.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data; Supported
                        placeholders: {HOME}, {CWD}, {TMP} (default: .)
  -e EXT, --extension EXT
                        The file extension to look for (incl dot), e.g.,
                        '.hdr'. (default: .hdr)
  --exclude [REGEXP ...]
                        The optional regular expression(s) for excluding ENVI
                        files to read (gets applied to file name, not path).
                        (default: None)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
