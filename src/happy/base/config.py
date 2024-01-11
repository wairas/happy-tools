import os


def get_config_dir() -> str:
    """
    Returns the config dir for happy. Creates the dir if necessary.

    :return: the config dir
    :rtype: str
    """
    home_dir = os.path.expanduser("~")
    result = os.path.join(home_dir, ".config", "happy")
    if not os.path.exists(result):
        os.makedirs(result)
    return result
