# matlab-reader

Reads data in HAPPY's Matlab format. 'normcube': spectral data, 'lambda': wave numbers, 'FinalMask': the pixel annotation mask, 'FinalMaskLabels': the mask pixel index -> label relation table

```
usage: matlab-reader [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                     [-A LOGGER_NAME] [-b BASE_DIR]

Reads data in HAPPY's Matlab format. 'normcube': spectral data, 'lambda': wave
numbers, 'FinalMask': the pixel annotation mask, 'FinalMaskLabels': the mask
pixel index -> label relation table

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data; Supported
                        placeholders: {HOME}, {CWD}, {TMP} (default: .)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
