# subtract-annotation-avg

Calculates the average spectrum from the specified annotation (uses outer bbox) and subtracts it from the data passing through.

```
usage: subtract-annotation-avg [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                               [-A LOGGER_NAME] [-f FILE] [--label LABEL]

Calculates the average spectrum from the specified annotation (uses outer
bbox) and subtracts it from the data passing through.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f FILE, --file FILE  The OPEX JSON file with annotations (default: None)
  --label LABEL         the annotation to use for calculating the average
                        (default: None)
```
