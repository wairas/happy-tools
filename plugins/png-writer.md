# png-writer

Generates PNG images from the data.

```
usage: png-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-A LOGGER_NAME] -b BASE_DIR [-R INT] [-G INT] [-B INT]
                  [-W INT] [-H INT] [-o OUTPUT]

Generates PNG images from the data.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: None)
  -R INT, --red_channel INT
                        The wave length to use for the red channel (default:
                        0)
  -G INT, --green_channel INT
                        The wave length to use for the green channel (default:
                        0)
  -B INT, --blue_channel INT
                        The wave length to use for the blue channel (default:
                        0)
  -W INT, --width INT   The custom width to use for the image; <=0 for the
                        default (default: 0)
  -H INT, --height INT  The custom height to use for the image; <=0 for the
                        default (default: 0)
  -o OUTPUT, --output OUTPUT
                        The pattern for the output files; The following
                        placeholders are available for the output pattern:
                        {SAMPLEID}, {BASEDIR}, {REPEAT} (default:
                        {BASEDIR}/{SAMPLEID}.{REPEAT}.png)
```
