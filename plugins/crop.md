# crop

Crops the data to the specified rectangle.

```
usage: crop [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
            [-x X] [-y Y] [-W WIDTH] [-H HEIGHT] [-p] [-v PAD_VALUE]

Crops the data to the specified rectangle.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -x X, --x X           The left of the cropping rectangle (default: 0)
  -y Y, --y Y           The top of the cropping rectangle (default: 0)
  -W WIDTH, --width WIDTH
                        The width of the cropping rectangle (default: 0)
  -H HEIGHT, --height HEIGHT
                        The height of the cropping rectangle (default: 0)
  -p, --pad             Whether to pad if necessary (default: False)
  -v PAD_VALUE, --pad_value PAD_VALUE
                        The value to pad with (default: 0)
```
