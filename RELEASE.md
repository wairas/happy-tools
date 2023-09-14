PyPi
====

Preparation:

* increment version in `setup.py`
* add new changelog section in `CHANGES.rst`
* ensure that help screens in `README.md` are up-to-date
* ensure that help screens on [hsi-website](https://github.com/wairas/hsi-website) are up-to-date
  * https://github.com/wairas/hsi-website/blob/main/docs/happy/happy_tools/envi-viewer.md
  * https://github.com/wairas/hsi-website/blob/main/docs/happy/happy_tools/happy-hsi2csv.md
  * https://github.com/wairas/hsi-website/blob/main/docs/happy/happy_tools/happy-hsi2rbg.md
  * https://github.com/wairas/hsi-website/blob/main/docs/happy/happy_tools/happy-opex2happy.md  
* commit/push all changes

Commands for releasing on pypi.org (requires twine >= 1.8.0):

```
find -name "*~" -delete
rm dist/*
./venv/bin/python setup.py clean
./venv/bin/python setup.py sdist
./venv/bin/twine upload dist/*
```


Github
======

Steps:

* start new release (version: `vX.Y.Z`)
* enter release notes, i.e., significant changes since last release
* upload `happy-tools-X.Y.Z.tar.gz` previously generated with `setyp.py`
* publish


