# norm-fixed

Uses the user-supplied min/max values to normalize the data. Values below or above get clipped.

```
usage: norm-fixed [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-A LOGGER_NAME] [-m NUM] [-M NUM]

Uses the user-supplied min/max values to normalize the data. Values below or
above get clipped.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -m NUM, --min NUM     The minimum value to use (default: 0.0)
  -M NUM, --max NUM     The maximum value to use (default: 10000.0)
```
