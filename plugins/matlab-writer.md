# matlab-writer

Writes data in Matlab format.

```
usage: matlab-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                     [-A LOGGER_NAME] -b BASE_DIR [-o OUTPUT]

Writes data in Matlab format.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: None)
  -o OUTPUT, --output OUTPUT
                        The pattern for the output files. (default:
                        {BASEDIR}/{SAMPLEID}.{REPEAT}.mat)
```
