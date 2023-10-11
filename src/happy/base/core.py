import importlib.util
import json
import sys

from typing import Dict
from seppl import get_class_name, get_class


def get_func(funcname: str):
    """
    Turns the function name into a function and returns it.

    :param funcname: the name of the function
    :type funcname: str
    :return: the function
    """
    parts = funcname.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def get_funcname(func: str):
    """
    Returns a string representation of a function name.

    :param func: the function to get the name for
    :return: the name
    """
    return func.__module__ + "." + func.__name__


def load_class(path: str, module_name: str, class_name: str) -> type:
    """
    Loads the specified class from the Python file.
    Based on: https://stackoverflow.com/a/67692/4698227

    :param path: the Python file to load
    :type path: str
    :param module_name: the name of the module to load the Python file as
    :type module_name: str
    :param class_name: the name of the class within the module
    :type class_name: str
    :return: the class
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


class ConfigurableObject:
    """
    Base class that returns its parameters as dictionary and can be initialized
    from a dictionary as well.
    """

    def to_dict(self) -> Dict:
        """
        Returns a dictionary with its parameters.

        :return: the parameters
        :rtype: dict
        """
        return {"class": get_class_name(self)}

    def to_json(self) -> str:
        """
        Returns the its representation as json string.

        :return: the generated json
        :rtype: str
        """
        return json.dumps(self.to_dict())

    def from_dict(self, d: Dict) -> 'ConfigurableObject':
        """
        Initializes its parameters from the provided dictionary.

        :param d: the parameters
        :type d: dict
        :return: returns itself
        :rtype: ConfigurableObject
        """
        return self

    @classmethod
    def create_from_dict(cls, d: Dict) -> 'ConfigurableObject':
        """
        Instantiates the pixel selector from the dictionary and returns it.

        :param d: the dictionary with the parameters
        :type d: dict
        :return: the pixel selector
        :rtype: PixelSelector
        """
        c = get_class(full_class_name=d["class"])
        obj = c()
        obj.from_dict(d)
        return obj

    @classmethod
    def from_json(cls, f) -> 'ConfigurableObject':
        """
        Instantiates and returns an object from the json data.

        :param f: the filename (str) or file-like object
        :return: the instantiated object
        """
        if isinstance(f, str):
            d = json.loads(f)
            return cls.create_from_dict(d)
        else:
            with open(f, "r") as fp:
                d = json.load(fp)
                return cls.create_from_dict(d)
