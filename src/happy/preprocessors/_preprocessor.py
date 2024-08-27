import abc
import argparse
import os

from typing import List, Optional

from seppl import split_args, split_cmdline, args_to_objects
from happy.base.core import PluginWithLogging
from happy.data import HappyData
from happy.base.registry import REGISTRY
from opex import ObjectPredictions


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

    def _do_fit(self, happy_data: HappyData):
        pass

    def fit(self, happy_data: HappyData):
        self._initialize()
        self._do_fit(happy_data)
        
    def _do_apply(self, happy_data: HappyData) -> List[HappyData]:
        raise NotImplementedError()

    def apply(self, happy_data: HappyData) -> List[HappyData]:
        self._initialize()
        return self._do_apply(happy_data)

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


def apply_preprocessor(happy_data: HappyData, method: 'Preprocessor') -> List[HappyData]:
    """
    Applies the preprocessing method to the data.

    :param happy_data: the data to process
    :type happy_data: HappyData
    :param method: the preprocessing method to apply
    :type method: Preprocessor
    :return: the list of processed data
    :rtype: list
    """
    method.fit(happy_data)
    new_happy_data = method.apply(happy_data)
    for item in new_happy_data:
        processing_note = {
            "preprocessing": [method.to_string()]
        }
        item.add_preprocessing_note(processing_note)

    return new_happy_data


class AbstractOPEXAnnotationsBasedPreprocessor(Preprocessor, abc.ABC):
    """
    Ancestor for methods that use an annotation rectangle.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self.params["annotations"] = None

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-f", "--file", metavar="FILE", type=str, help="The OPEX JSON file with annotations", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.params["annotations"] = None
        if ns.file is not None:
            anns = ObjectPredictions.load_json_from_file(ns.file)
            self.params["annotations"] = anns

    @property
    def annotations(self):
        """
        Returns the current OPEX annotations.

        :return: the OPEX annotations
        :rtype: ObjectPredictions
        """
        return self.params["annotations"]

    @annotations.setter
    def annotations(self, anns):
        """
        Sets the OPEX annotations to use.

        :param anns: the OPEX annotations to use
        :type anns: ObjectPredictions
        """
        self.params["annotations"] = anns

    def _initialize(self):
        """
        Hook method for initializing the black reference method.
        """
        super()._initialize()
        if self.params["annotations"] is None:
            self.logger().error("No OPEX annotations set!")
        else:
            if not isinstance(self.params["annotations"], ObjectPredictions):
                raise Exception("Annotations are not of type %s: %s" % (str(ObjectPredictions), str(type(self.params["annotation"]))))
