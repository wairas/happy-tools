from typing import Dict, Union, List

from seppl import ClassListerRegistry, Plugin

# the default modules to look for plugins
HAPPY_DEFAULT_CLASS_LISTERS = [
    "happy.base.class_lister",
]

# the environment variable to use for overriding the default modules
HAPPY_ENV_CLASS_LISTERS = "HAPPY_CLASS_LISTERS"

# the environment variable to use for excluding modules
HAPPY_ENV_CLASS_LISTERS_EXCL = "HAPPY_CLASS_LISTERS_EXCL"


class HappyRegistry(ClassListerRegistry):
    """
    Custom Registry class for the HAPPy tools.
    """

    def __init__(self, default_class_listers: Union[str, List[str]] = None, env_class_listers: str = None,
                 excluded_class_listers: Union[str, List[str]] = None, env_excluded_class_listers: str = None):
        """

        :param default_class_listers: the default class lister to use for registering plugins
        :type default_class_listers: str or list
        :param env_class_listers: the environment variable to retrieve the class listers from (overrides default ones)
        :type env_class_listers: str
        :param excluded_class_listers: the class listers to exclude from registering plugins, ignored if None
        :type excluded_class_listers: str or list
        :param env_excluded_class_listers: the environment variable to retrieve the excluded class listers from (overrides manually set ones)
        :type env_excluded_class_listers: str
        """
        super().__init__(default_class_listers=default_class_listers,
                         env_class_listers=env_class_listers,
                         excluded_class_listers=excluded_class_listers,
                         env_excluded_class_listers=env_excluded_class_listers)

    def all_plugins(self) -> Dict[str, Plugin]:
        """
        Returns all available plugins.

        :return: the dictionary of all plugins (name / plugin)
        :rtype: dict
        """
        result = dict()
        result.update(self.blackref_methods())
        result.update(self.happydata_readers())
        result.update(self.happydata_writers())
        result.update(self.normalizations())
        result.update(self.pixel_selectors())
        result.update(self.preprocessors())
        result.update(self.ref_locators())
        result.update(self.region_extractors())
        result.update(self.whiteref_methods())
        return result

    def blackref_methods(self) -> Dict[str, Plugin]:
        """
        Returns all the black reference methods.

        :return: the dictionary of black reference methods (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.data.black_ref._core.AbstractBlackReferenceMethod", fail_if_empty=False)

    def whiteref_methods(self) -> Dict[str, Plugin]:
        """
        Returns all the white reference methods.

        :return: the dictionary of white reference methods (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.data.white_ref._core.AbstractWhiteReferenceMethod", fail_if_empty=False)

    def ref_locators(self) -> Dict[str, Plugin]:
        """
        Returns all the reference locators.

        :return: the dictionary of ref locators (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.data.ref_locator._core.AbstractReferenceLocator", fail_if_empty=False)

    def normalizations(self) -> Dict[str, Plugin]:
        """
        Returns all the normalization schemes.

        :return: the dictionary of normalization schemes (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.data.normalization._core.AbstractNormalization", fail_if_empty=False)

    def happydata_readers(self) -> Dict[str, Plugin]:
        """
        Returns all the readers for happydata data structure.

        :return: the dictionary of readers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.readers._happydata_reader.HappyDataReader", fail_if_empty=False)

    def preprocessors(self) -> Dict[str, Plugin]:
        """
        Returns all the preprocessors.

        :return: the dictionary of preprocessors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.preprocessors._preprocessor.Preprocessor", fail_if_empty=False)

    def happydata_writers(self) -> Dict[str, Plugin]:
        """
        Returns all the writers for happydata data structure.

        :return: the dictionary of writers (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.writers._happydata_writer.HappyDataWriter", fail_if_empty=False)

    def pixel_selectors(self) -> Dict[str, Plugin]:
        """
        Returns all the pixel selectors.

        :return: the dictionary of pixel selectors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.pixel_selectors._pixel_selector.PixelSelector", fail_if_empty=False)

    def region_extractors(self) -> Dict[str, Plugin]:
        """
        Returns all the region extractors.

        :return: the dictionary of region extractors (name / plugin)
        :rtype: dict
        """
        # class via string to avoid circular imports
        return self.plugins("happy.region_extractors._region_extractor.RegionExtractor", fail_if_empty=False)


# singleton of the Registry
REGISTRY = HappyRegistry(default_class_listers=HAPPY_DEFAULT_CLASS_LISTERS,
                         env_class_listers=HAPPY_ENV_CLASS_LISTERS,
                         excluded_class_listers=None,
                         env_excluded_class_listers=HAPPY_ENV_CLASS_LISTERS_EXCL)


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
