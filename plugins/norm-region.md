# norm-region

Uses the min/max values determined from the specified region to normalize the data. Values below or above get clipped.

```
usage: norm-region [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [-A LOGGER_NAME] [--x0 COORD] [--y0 COORD] [--x1 COORD]
                   [--y1 COORD]

Uses the min/max values determined from the specified region to normalize the
data. Values below or above get clipped.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  --x0 COORD            The 0-based left coordinate of the region (default: 0)
  --y0 COORD            The 0-based top coordinate of the region (default: 0)
  --x1 COORD            The 0-based right coordinate of the region, use -1 for
                        the edge of the image (default: -1)
  --y1 COORD            The 0-based bottom coordinate of the region, use -1
                        for the edge of the image (default: -1)
```
