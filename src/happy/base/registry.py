from typing import Dict
from seppl import Registry, Plugin, MODE_DYNAMIC


# the default modules to look for plugins
HAPPY_DEFAULT_MODULES = ",".join(
    [
        "happy.readers",
        "happy.preprocessors",
        "happy.writers",
        "happy.pixel_selectors",
        "happy.region_extractors",
    ])

# the environment variable to use for overriding the default modules
HAPPY_ENV_MODULES = "HAPPY_MODULES"

# the known entrypoints in setup.py
ENTRYPOINT_HAPPYDATA_READERS = "happy.happydata_readers"
ENTRYPOINT_PREPROCESSORS = "happy.preprocessors"
ENTRYPOINT_HAPPYDATA_WRITERS = "happy.happydata_writers"
ENTRYPOINT_PIXEL_SELECTORS = "happy.pixel_selectors"
ENTRYPOINT_REGION_EXTRACTORS = "happy.region_extractors"


class HappyRegistry(Registry):
    """
    Custom Registry class for the HAPPy tools.
    """

    def __init__(self, default_modules=HAPPY_DEFAULT_MODULES,
                 env_modules=HAPPY_ENV_MODULES):
        super().__init__(mode=MODE_DYNAMIC,
                         default_modules=default_modules,
                         env_modules=env_modules,
                         enforce_uniqueness=True)

    def happydata_readers(self) -> Dict[str, Plugin]:
        """
        Returns all the readers for happydata data structure.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_HAPPYDATA_READERS, Plugin)

    def preprocessors(self) -> Dict[str, Plugin]:
        """
        Returns all the preprocessors.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_PREPROCESSORS, Plugin)

    def happydata_writers(self) -> Dict[str, Plugin]:
        """
        Returns all the writers for happydata data structure.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_HAPPYDATA_WRITERS, Plugin)

    def pixel_selectors(self) -> Dict[str, Plugin]:
        """
        Returns all the pixel selectors.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_PIXEL_SELECTORS, Plugin)

    def region_extractors(self) -> Dict[str, Plugin]:
        """
        Returns all the pixel selectors.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_REGION_EXTRACTORS, Plugin)


# singleton of the Registry
REGISTRY = HappyRegistry()

