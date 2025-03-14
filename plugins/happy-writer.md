# happy-writer

Writes data in HAPPy format.

```
usage: happy-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [-A LOGGER_NAME] [-b BASE_DIR]

Writes data in HAPPy format.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: .)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
