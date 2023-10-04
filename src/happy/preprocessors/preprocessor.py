import abc
from seppl import Plugin, split_args, split_cmdline, args_to_objects
from happy.base.registry import REGISTRY


class Preprocessor(Plugin, abc.ABC):
    
    def __init__(self, **kwargs):
        self.params = kwargs
        # Handle additional positional arguments if needed

    def _initialize(self):
        """
        For checks and obtaining variables from self.params.
        """
        pass

    def _do_fit(self, data, metadata=None):
        return self

    def fit(self, data, metadata=None):
        self._initialize()
        return self._do_fit(data, metadata=metadata)
        
    def _do_apply(self, data, metadata=None):
        raise NotImplementedError()

    def apply(self, data, metadata=None):
        self._initialize()
        return self._do_apply(data, metadata=metadata)

    def __str__(self):
        return self.to_string()

    def to_string(self):
        # Get the class name
        class_name = self.__class__.__name__

        # Get the arguments from the 'params' dictionary
        arguments = ", ".join(f"{key}={value}" for key, value in self.params.items())

        return f"{class_name}({arguments})"

    @classmethod
    def parse_preprocessors(cls, cmdline):
        """
        Splits the command-line, parses the arguments, instantiates and returns the preprocessors.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the preprocessor plugin list
        :rtype: list
        """
        plugins = REGISTRY.preprocessors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        return args_to_objects(args, plugins, allow_global_options=False)
