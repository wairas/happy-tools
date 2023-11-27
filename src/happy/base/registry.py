from typing import Dict
from seppl import Registry, Plugin, MODE_DYNAMIC, get_class


# the default modules to look for plugins
HAPPY_DEFAULT_MODULES = ",".join(
    [
        "happy.data.black_ref",
        "happy.data.white_ref",
        "happy.data.ref_locator",
        "happy.readers",
        "happy.preprocessors",
        "happy.writers",
        "happy.pixel_selectors",
        "happy.region_extractors",
    ])

# the environment variable to use for overriding the default modules
HAPPY_ENV_MODULES = "HAPPY_MODULES"

# the environment variable to use for excluding modules
HAPPY_ENV_MODULES_EXCL = "HAPPY_MODULES_EXCL"

# the known entrypoints in setup.py
ENTRYPOINT_BLACKREF_METHODS = "happy.blackref_methods"
ENTRYPOINT_WHITEREF_METHODS = "happy.whiteref_methods"
ENTRYPOINT_REF_LOCATOR = "happy.ref_locator"
ENTRYPOINT_HAPPYDATA_READERS = "happy.happydata_readers"
ENTRYPOINT_PREPROCESSORS = "happy.preprocessors"
ENTRYPOINT_HAPPYDATA_WRITERS = "happy.happydata_writers"
ENTRYPOINT_PIXEL_SELECTORS = "happy.pixel_selectors"
ENTRYPOINT_REGION_EXTRACTORS = "happy.region_extractors"
ENTRYPOINTS = [
    ENTRYPOINT_BLACKREF_METHODS,
    ENTRYPOINT_WHITEREF_METHODS,
    ENTRYPOINT_REF_LOCATOR,
    ENTRYPOINT_HAPPYDATA_READERS,
    ENTRYPOINT_PREPROCESSORS,
    ENTRYPOINT_HAPPYDATA_WRITERS,
    ENTRYPOINT_PIXEL_SELECTORS,
    ENTRYPOINT_REGION_EXTRACTORS,
]


class HappyRegistry(Registry):
    """
    Custom Registry class for the HAPPy tools.
    """

    def __init__(self, default_modules=HAPPY_DEFAULT_MODULES,
                 env_modules=HAPPY_ENV_MODULES,
                 excluded_modules=None,
                 excluded_env_modules=HAPPY_ENV_MODULES_EXCL):
        """

        :param default_modules: the default modules to use for registering plugins, comma-separated string of module names or list of module names
        :type default_modules: str or list
        :param env_modules: the environment variable to retrieve the modules from (overrides default ones)
        :type env_modules: str
        :param excluded_modules: the modules to exclude from registering plugins, comma-separated string of module names or list of module names, ignored if None
        :type excluded_modules: str or list
        :param excluded_env_modules: the environment variable to retrieve the excluded modules from (overrides manually set ones)
        :type excluded_env_modules: str
        """
        super().__init__(mode=MODE_DYNAMIC,
                         default_modules=default_modules,
                         env_modules=env_modules,
                         excluded_modules=excluded_modules,
                         excluded_env_modules=excluded_env_modules,
                         enforce_uniqueness=True)

    def all_plugins(self) -> Dict[str, Plugin]:
        """
        Returns all available plugins.

        :return: the dictionary of all plugins (name / plugin)
        :rtype: dict
        """
        result = dict()
        for entrypoint in ENTRYPOINTS:
            plugins = self.plugins(entrypoint)
            result.update(plugins)
        return result

    def blackref_methods(self) -> Dict[str, Plugin]:
        """
        Returns all the black reference methods.

        :return: the dictionary of readers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_BLACKREF_METHODS, get_class("happy.data.black_ref._core.AbstractBlackReferenceMethod"))

    def whiteref_methods(self) -> Dict[str, Plugin]:
        """
        Returns all the white reference methods.

        :return: the dictionary of readers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_WHITEREF_METHODS, get_class("happy.data.white_ref._core.AbstractWhiteReferenceMethod"))

    def ref_locators(self) -> Dict[str, Plugin]:
        """
        Returns all the reference locators.

        :return: the dictionary of readers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_REF_LOCATOR, get_class("happy.data.ref_locator._core.AbstractReferenceLocator"))

    def happydata_readers(self) -> Dict[str, Plugin]:
        """
        Returns all the readers for happydata data structure.

        :return: the dictionary of readers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_HAPPYDATA_READERS, get_class("happy.readers._happydata_reader.HappyDataReader"))

    def preprocessors(self) -> Dict[str, Plugin]:
        """
        Returns all the preprocessors.

        :return: the dictionary of preprocessors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_PREPROCESSORS, get_class("happy.preprocessors._preprocessor.Preprocessor"))

    def happydata_writers(self) -> Dict[str, Plugin]:
        """
        Returns all the writers for happydata data structure.

        :return: the dictionary of writers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_HAPPYDATA_WRITERS, get_class("happy.writers._happydata_writer.HappyDataWriter"))

    def pixel_selectors(self) -> Dict[str, Plugin]:
        """
        Returns all the pixel selectors.

        :return: the dictionary of pixel selectors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_PIXEL_SELECTORS, get_class("happy.pixel_selectors._pixel_selector.PixelSelector"))

    def region_extractors(self) -> Dict[str, Plugin]:
        """
        Returns all the region extractors.

        :return: the dictionary of region extractors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins(ENTRYPOINT_REGION_EXTRACTORS, get_class("happy.region_extractors._region_extractor.RegionExtractor"))


# singleton of the Registry
REGISTRY = HappyRegistry()


def print_help_all():
    """
    Prints the help for all plugins.
    """
    plugins = REGISTRY.all_plugins()
    keys = sorted(plugins.keys())
    for key in keys:
        print()
        print(plugins[key].name())
        print("=" * len(plugins[key].name()))
        print()
        print(plugins[key].format_help())


def print_help(plugin_name: str):
    """
    Prints the help for the specified plugin.

    :param plugin_name: the name of the plugin to print the help for
    :type plugin_name: str
    """
    plugins = REGISTRY.all_plugins()
    if plugin_name in plugins:
        print()
        print(plugins[plugin_name].name())
        print("=" * len(plugins[plugin_name].name()))
        print()
        print(plugins[plugin_name].format_help())
    else:
        keys = sorted(plugins.keys())
        print()
        print("Unknown plugin name: %s" % plugin_name)
        print()
        print("Available plugins: %s" % ", ".join(keys))
        print()
