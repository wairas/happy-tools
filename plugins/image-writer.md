# image-writer

Generates images from the data. The type of image is determined by the extension of the output files pattern.

```
usage: image-writer [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [-A LOGGER_NAME] [-b BASE_DIR] [-o OUTPUT] [-R INT]
                    [-G INT] [-B INT] [-W INT] [-H INT] [-N PLUGIN]
                    [--suppress_metadata]

Generates images from the data. The type of image is determined by the
extension of the output files pattern.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: .)
  -o OUTPUT, --output OUTPUT
                        The pattern for the output files; The following
                        placeholders are available for the output pattern:
                        {BASEDIR}, {SAMPLEID}, {REPEAT}, {REGION} (default:
                        {BASEDIR}/{SAMPLEID}.{REPEAT}.png)
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
  -N PLUGIN, --normalization PLUGIN
                        The normalization plugin and its options to use
                        (default: norm-simple)
  --suppress_metadata   Whether to suppress the output of the meta-data
                        (default: False)
```
