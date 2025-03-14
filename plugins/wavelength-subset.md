# wavelength-subset

Returns the specified subset of wavelengths.

```
usage: wavelength-subset [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                         [-A LOGGER_NAME]
                         [-s SUBSET_INDICES [SUBSET_INDICES ...]]
                         [-f FROM_INDEX] [-t TO_INDEX]

Returns the specified subset of wavelengths.

options:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -s SUBSET_INDICES [SUBSET_INDICES ...], --subset_indices SUBSET_INDICES [SUBSET_INDICES ...]
                        The explicit 0-based wavelength indices to use
                        (default: None)
  -f FROM_INDEX, --from_index FROM_INDEX
                        The first 0-based wavelength to include (default: 60)
  -t TO_INDEX, --to_index TO_INDEX
                        The last 0-based wavelength to include (default: 189)
```
