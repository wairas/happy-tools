# ps-multi

Combines multiple pixel-selectors.

```
usage: ps-multi [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
                [-s [SELECTORS [SELECTORS ...]]]

Combines multiple pixel-selectors.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -s [SELECTORS [SELECTORS ...]], --selectors [SELECTORS [SELECTORS ...]]
                        The command-lines of the base pixel-selectors to use.
                        (default: None)
```
