# extract-regions

Applies the specified region extractor to extract (sub-)regions from the incoming data.

```
usage: extract-regions [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                       [-A LOGGER_NAME] [-r REGION_EXTRACTOR]

Applies the specified region extractor to extract (sub-)regions from the
incoming data.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -r REGION_EXTRACTOR, --region_extractor REGION_EXTRACTOR
                        The command-line of the region-extractor to apply
                        (default: re-full)
```
