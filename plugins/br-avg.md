# br-avg

Black reference method that computes the average per band. Does not require scan and reference to have the same size.

```
usage: br-avg [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
              [-f REFERENCE_FILE]

Black reference method that computes the average per band. Does not require
scan and reference to have the same size.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -f REFERENCE_FILE, --reference_file REFERENCE_FILE
                        The ENVI reference file to load (default: None)
```
