# happy-reader

Reads data in HAPPy format.

```
usage: happy-reader [-h] -b BASE_DIR [-r [FILENAME [FILENAME ...]]] [-w FILE]

Reads data in HAPPy format.

optional arguments:
  -h, --help            show this help message and exit
  -b BASE_DIR, --base_dir BASE_DIR
                        The base directory for the data (default: None)
  -r [FILENAME [FILENAME ...]], --restrict_metadata [FILENAME [FILENAME ...]]
                        The meta-data files to restrict to, omit to use all
                        (default: None)
  -w FILE, --wavelength_override_file FILE
                        A file with the wavelengths to use instead of the ones
                        read from the actual ENVI files, can be either an
                        ENVI-like file or a text file with one wavelength per
                        line. (default: None)
```
