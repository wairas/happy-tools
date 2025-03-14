# sni

Spectral noise interpolation. For each pixel it looks at the gradient between wavelengths and compares it against the average gradient of surrounding pixels. If that difference is larger than the specified threshold (= noisy) then interpolate this wavelength.

```
usage: sni [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
           [-t THRESHOLD]

Spectral noise interpolation. For each pixel it looks at the gradient between
wavelengths and compares it against the average gradient of surrounding
pixels. If that difference is larger than the specified threshold (= noisy)
then interpolate this wavelength.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -t THRESHOLD, --threshold THRESHOLD
                        The threshold for identifying noisy pixels. (default:
                        0.8)
```
