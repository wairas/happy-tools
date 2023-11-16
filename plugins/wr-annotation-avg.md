# wr-annotation-avg

Computes the average per band in the annotation rectangle. Does not require scan and reference to have the same size.

```
usage: wr-annotation-avg [-h] [-f REFERENCE_FILE] [-a COORD COORD COORD COORD]

Computes the average per band in the annotation rectangle. Does not require
scan and reference to have the same size.

optional arguments:
  -h, --help            show this help message and exit
  -f REFERENCE_FILE, --reference_file REFERENCE_FILE
                        The ENVI reference file to load (default: None)
  -a COORD COORD COORD COORD, --annotation COORD COORD COORD COORD
                        The annotation rectangle (top, left, bottom, right)
                        (default: None)
```
