# pad

Pads the data to the specified dimensions with the supplied value

```
usage: pad [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
           [-W WIDTH] [-H HEIGHT] [-v PAD_VALUE]

Pads the data to the specified dimensions with the supplied value

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -W WIDTH, --width WIDTH
                        The width to pad to (default: 0)
  -H HEIGHT, --height HEIGHT
                        The height to pad to (default: 0)
  -v PAD_VALUE, --pad_value PAD_VALUE
                        The value to pad with (default: 0)
```
