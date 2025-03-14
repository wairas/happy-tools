# rl-file-pattern

Reference locator that uses the supplied pattern and applies that to the incoming scan file name to generate the reference file name.

```
usage: rl-file-pattern [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                       [-A LOGGER_NAME] [-m] [-p PATTERN]

Reference locator that uses the supplied pattern and applies that to the
incoming scan file name to generate the reference file name.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -m, --must_exist      Whether the determined reference file must exist
                        (default: False)
  -p PATTERN, --pattern PATTERN
                        The pattern to use for generating a reference file
                        name from the scan file; available placeholders:
                        {PATH}, {NAME}, {EXT} (default: {PATH}/{NAME}{EXT})
```
