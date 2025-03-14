# down-sample

Data reduction preprocessor that takes every x-th pixel on the x-axis and y-th pixel on the y-axis.

```
usage: down-sample [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [-A LOGGER_NAME] [-x XTH] [-y YTH]

Data reduction preprocessor that takes every x-th pixel on the x-axis and y-th
pixel on the y-axis.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -x XTH, --xth XTH     Every nth pixel on the x axis (default: 2)
  -y YTH, --yth YTH     Every nth pixel on the y axis (default: 2)
```
