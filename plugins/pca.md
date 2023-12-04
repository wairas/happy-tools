# pca

Applies principal components analysis to the data.

```
usage: pca [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A LOGGER_NAME]
           [-n COMPONENTS] [-p PERCENT_PIXELS] [-l LOAD] [-s SAVE]

Applies principal components analysis to the data.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -n COMPONENTS, --components COMPONENTS
                        The number of PCA components (default: 5)
  -p PERCENT_PIXELS, --percent_pixels PERCENT_PIXELS
                        The subset of pixels to use (0-100) (default: 100.0)
  -l LOAD, --load LOAD  The file with the pickled sklearn PCA instance to load
                        and use instead of building one each time data is
                        passing through (default: None)
  -s SAVE, --save SAVE  The file to save the fitted sklearn PCA instance to
                        (default: None)
```
