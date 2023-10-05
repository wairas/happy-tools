from typing import Dict
from seppl import Registry, Plugin


# the default modules to look for plugins
HAPPY_DEFAULT_MODULES = ",".join(
    [
        "happy.preprocessors",
    ])

# the environment variable to use for overriding the default modules
HAPPY_ENV_MODULES = "HAPPY_MODULES"

# the known entrypoints in setup.py
ENTRYPOINT_PREPROCESSORS = "happy.preprocessors"


class HappyRegistry(Registry):
    """
    Custom Registry class for the HAPPy tools.
    """

    def __init__(self, default_modules=HAPPY_DEFAULT_MODULES,
                 env_modules=HAPPY_ENV_MODULES):
        super().__init__(default_modules=default_modules,
                         env_modules=env_modules,
                         enforce_uniqueness=True)

    def preprocessors(self) -> Dict[str, Plugin]:
        """
        Returns all the preprocessors.

        :return: dict
        """
        return self.plugins(ENTRYPOINT_PREPROCESSORS, Plugin)


# singleton of the Registry
REGISTRY = HappyRegistry()
