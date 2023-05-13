import inspect
import json


def get_class(classname):
    """
    Returns the class object associated with the dot-notation classname.

    Taken from here: http://stackoverflow.com/a/452981

    :param classname: the classname
    :type classname: str
    :return: the class object
    """
    parts = classname.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def get_classname(obj):
    """
    Returns the classname of the JB_Object, Python class or object.

    :param obj: the java object or Python class/object to get the classname for
    :type obj: object
    :return: the classname
    :rtype: str
    """
    if inspect.isclass(obj):
        return obj.__module__ + "." + obj.__name__
    else:
        return get_classname(obj.__class__)


def get_func(funcname):
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


def get_funcname(func):
    """
    Returns a string representation of a function name.

    :param func: the function to get the name for
    :return: the name
    """
    return func.__module__ + "." + func.__name__


class ConfigurableObject:
    """
    Base class that returns its parameters as dictionary and can be initialized
    from a dictionary as well.
    """

    def to_dict(self):
        """
        Returns a dictionary with its parameters.

        :return: the parameters
        :rtype: dict
        """
        return {"class": get_classname(self)}

    def from_dict(self, d):
        """
        Initializes its parameters from the provided dictionary.

        :param d: the parameters
        :type d: dict
        """
        pass

    @classmethod
    def create_from_dict(cls, d):
        """
        Instantiates the pixel selector from the dictionary and returns it.

        :param d: the dictionary with the parameters
        :type d: dict
        :return: the pixel selector
        :rtype: PixelSelector
        """
        c = get_class(d["class"])
        obj = c()
        obj.from_dict(d)
        return obj

    @classmethod
    def from_json(cls, f):
        """
        Instantiates and returns an object from the json data.

        :param f: the filename (str) or file-like object
        :return: the instantiated object
        """
        if isinstance(f, str):
            with open(f, "r") as fp:
                d = json.load(fp)
                return cls.create_from_dict(d)
        else:
            d = json.load(f)
            return cls.create_from_dict(d)
