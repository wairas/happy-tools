# re-grid

Splits the data into a grid of the specified region size.

```
usage: re-grid [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
               [-t TARGET_NAME] -r REGION_SIZE REGION_SIZE [-T]

Splits the data into a grid of the specified region size.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -t TARGET_NAME, --target_name TARGET_NAME
                        The name of the target value (default: None)
  -r REGION_SIZE REGION_SIZE, --region_size REGION_SIZE REGION_SIZE
                        The width and height of the region (default: None)
  -T, --truncate_regions
                        Whether to truncate the regions (default: False)
```
