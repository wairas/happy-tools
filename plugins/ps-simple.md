# ps-simple

Returns the spectrum at the requested x/y location.

```
usage: ps-simple [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                 [-A LOGGER_NAME] -n N [-c CRITERIA] [-b]

Returns the spectrum at the requested x/y location.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -n N                  The number of pixels (default: None)
  -c CRITERIA, --criteria CRITERIA
                        The JSON string defining the criteria to apply
                        (default: None)
  -b, --include_background
                        Whether to include the background (default: False)
```
