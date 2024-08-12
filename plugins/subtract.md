# subtract

Subtracts the specified ENVI file from the data passing through.

```
usage: subtract [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
                [-f FILE]

Subtracts the specified ENVI file from the data passing through.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f FILE, --file FILE  the ENVI file to subtract from the data passing
                        through (default: .)
```
