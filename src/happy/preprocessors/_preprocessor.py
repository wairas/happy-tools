import abc
import os

from seppl import split_args, split_cmdline, args_to_objects
from happy.base.core import PluginWithLogging
from happy.base.registry import REGISTRY
from typing import List, Optional


class Preprocessor(PluginWithLogging, abc.ABC):
    
    def __init__(self, **kwargs):
        super().__init__()
        self.params = dict()
        self.parse_args([])
        self.params.update(kwargs)

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

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        # Get the class name
        class_name = self.__class__.__name__

        # Get the arguments from the 'params' dictionary
        arguments = ", ".join(f"{key}={value}" for key, value in self.params.items())

        return f"{class_name}({arguments})"

    @classmethod
    def parse_preprocessor(cls, cmdline: str) -> Optional['Preprocessor']:
        """
        Splits the command-line, parses the arguments, instantiates and returns the preprocessor.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the preprocessor, None if not exactly one selector parsed
        :rtype: Preprocessor
        """
        plugins = REGISTRY.preprocessors()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        l = args_to_objects(args, plugins, allow_global_options=False)
        if len(l) == 1:
            return l[0]
        else:
            return None

    @classmethod
    def parse_preprocessors(cls, cmdline: str) -> List:
        """
        Splits the command-line, parses the arguments, instantiates and returns the preprocessors.
        If pointing to a file, reads one preprocessor per line, instantiates and returns them.
        Empty lines or lines starting with # get ignored.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the preprocessor plugin list
        :rtype: list
        """
        if os.path.exists(cmdline) and os.path.isfile(cmdline):
            result = []
            with open(cmdline) as fp:
                for line in fp.readlines():
                    line = line.strip()
                    # empty?
                    if len(line) == 0:
                        continue
                    # comment?
                    if line.startswith("#"):
                        continue
                    pp = cls.parse_preprocessor(line.strip())
                    if pp is not None:
                        result.append(pp)
            return result
        else:
            plugins = REGISTRY.preprocessors()
            args = split_args(split_cmdline(cmdline), plugins.keys())
            return args_to_objects(args, plugins, allow_global_options=False)
