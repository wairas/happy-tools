# norm-object-annotations

Normalization that only uses pixels from annotations (white/black references are always skipped) to calculate the min/max/range.

```
usage: norm-object-annotations [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                               [-A LOGGER_NAME] [-l [LABEL [LABEL ...]]]

Normalization that only uses pixels from annotations (white/black references
are always skipped) to calculate the min/max/range.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -l [LABEL [LABEL ...]], --label [LABEL [LABEL ...]]
                        The labels to restrict the calculation to rather than
                        all (except white/black reference) (default: None)
```
