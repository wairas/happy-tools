# ps-column-wise

Calculates the average of randomly selected pixels per column.

```
usage: ps-column-wise [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                      [-A LOGGER_NAME] -n N [-c CRITERIA] [-b] [-C COLUMN]

Calculates the average of randomly selected pixels per column.

optional arguments:
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
  -C COLUMN, --column COLUMN
                        The column to select pixels from (0-based index).
                        (default: 0)
```
