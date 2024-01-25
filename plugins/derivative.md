# derivative

Applies Savitzky-Golay to the data.

```
usage: derivative [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-A LOGGER_NAME] [-w WINDOW_LENGTH] [-p POLYORDER]
                  [-d DERIV]

Applies Savitzky-Golay to the data.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -w WINDOW_LENGTH, --window_length WINDOW_LENGTH
                        The size of the window (must be odd number) (default:
                        5)
  -p POLYORDER, --polyorder POLYORDER
                        The polynominal order (default: 2)
  -d DERIV, --deriv DERIV
                        The deriviative to use, 0 is just smoothing (default:
                        1)
```
