# norm-fixed

Uses the user-supplied min/max values to normalize the data. Values below or above get clipped.

```
usage: norm-fixed [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-A LOGGER_NAME] [-m NUM] [-M NUM] [-r NUM] [-R NUM]
                  [-g NUM] [-G NUM] [-b NUM] [-B NUM]

Uses the user-supplied min/max values to normalize the data. Values below or
above get clipped.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -m NUM, --min NUM     The minimum value to use, default for all channels
                        (default: 0.0)
  -M NUM, --max NUM     The maximum value to use, default for all channels
                        (default: 10000.0)
  -r NUM, --red_min NUM
                        The minimum value to use for the red channel (default:
                        None)
  -R NUM, --red_max NUM
                        The maximum value to use for the red channel (default:
                        None)
  -g NUM, --green_min NUM
                        The minimum value to use for the green channel
                        (default: None)
  -G NUM, --green_max NUM
                        The maximum value to use for the green channel
                        (default: None)
  -b NUM, --blue_min NUM
                        The minimum value to use for the blue channel
                        (default: None)
  -B NUM, --blue_max NUM
                        The maximum value to use for the blue channel
                        (default: None)
```
