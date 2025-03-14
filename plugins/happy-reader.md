# happy-reader

Reads data in HAPPy format.

```
usage: happy-reader [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [-A LOGGER_NAME] [-b BASE_DIR] [-r [FILENAME ...]]
                    [-w FILE]

Reads data in HAPPy format.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data; Supported
                        placeholders: {HOME}, {CWD}, {TMP} (default: .)
  -r [FILENAME ...], --restrict_metadata [FILENAME ...]
                        The meta-data files to restrict to, omit to use all
                        (default: None)
  -w FILE, --wavelength_override_file FILE
                        A file with the wavelengths to use instead of the ones
                        read from the actual ENVI files, can be either an
                        ENVI-like file or a text file with one wavelength per
                        line. (default: None)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
