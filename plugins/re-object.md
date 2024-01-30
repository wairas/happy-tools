# re-object

Extracts a region around objects with the specified object-data key in the meta-data.

```
usage: re-object [-h] [-V {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                 [-A LOGGER_NAME] [-t TARGET_NAME]
                 [-r REGION_SIZE REGION_SIZE] [-k OBJECT_KEY] [-o OBJ_VALUES]
                 [-c [BASE_CRITERIA [BASE_CRITERIA ...]]]

Extracts a region around objects with the specified object-data key in the
meta-data.

optional arguments:
  -h, --help            show this help message and exit
  -V {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -A LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger (default: None)
  -t TARGET_NAME, --target_name TARGET_NAME
                        The name of the target value (default: None)
  -r REGION_SIZE REGION_SIZE, --region_size REGION_SIZE REGION_SIZE
                        The width and height of the region (default: [128,
                        128])
  -k OBJECT_KEY, --object_key OBJECT_KEY
                        The object key in the meta-data (default: None)
  -o OBJ_VALUES, --obj_values OBJ_VALUES
                        The object values to look for (supplied as JSON array
                        string) (default: [])
  -c [BASE_CRITERIA [BASE_CRITERIA ...]], --base_criteria [BASE_CRITERIA [BASE_CRITERIA ...]]
                        The criteria (JSON string or filename) to apply
                        (default: [])
```
