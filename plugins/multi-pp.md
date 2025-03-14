# multi-pp

Combines multiple pre-processors.

```
usage: multi-pp [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
                [-p PREPROCESSORS]

Combines multiple pre-processors.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -p PREPROCESSORS, --preprocessors PREPROCESSORS
                        The preprocessors to wrap. Either preprocessor
                        command-line(s) or file with one preprocessor command-
                        line per line. (default: None)
```
