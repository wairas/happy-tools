# rl-fixed

Reference locator that always returns the specified reference file name.

```
usage: rl-fixed [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
                [-f FILE]

Reference locator that always returns the specified reference file name.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f FILE, --reference_file FILE
                        The fixed reference file to use. (default: None)
```
