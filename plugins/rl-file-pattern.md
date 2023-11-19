# rl-file-pattern

Reference locator that uses the supplied pattern and applies that to the incoming scan file name to generate the reference file name.

```
usage: rl-file-pattern [-h] [-p PATTERN]

Reference locator that uses the supplied pattern and applies that to the
incoming scan file name to generate the reference file name.

optional arguments:
  -h, --help            show this help message and exit
  -p PATTERN, --pattern PATTERN
                        The pattern to use for generating a reference file
                        name from the scan file; available placeholders:
                        {PATH}, {NAME}, {EXT} (default: {PATH}/{NAME}{EXT})
```
