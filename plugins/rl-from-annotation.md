# rl-from-annotation

Reference locator that uses the label to identify the annotation to use as reference data (returns OPEX bbox).

```
usage: rl-from-annotation [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                          [-A LOGGER_NAME] [-l LABEL]

Reference locator that uses the label to identify the annotation to use as
reference data (returns OPEX bbox).

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -l LABEL, --label LABEL
                        The label of the annotation to use as reference data
                        (default: None)
```
