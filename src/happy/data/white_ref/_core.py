import abc
import argparse
import spectral.io.envi as envi

from happy.base.registry import REGISTRY
from happy.base.core import PluginWithLogging
from seppl import split_args, split_cmdline, args_to_objects

""" the label to use for the white reference annotation. """


class AbstractWhiteReferenceMethod(PluginWithLogging, abc.ABC):
    """
    Ancestor for methods that apply a white reference to scans.
    """

    def __init__(self):
        """
        Basic initialization of the white reference method.
        """
        super().__init__()
        self._initialized = False
        self._reference = None
        self.parse_args([])

    def _reset(self):
        """
        Resets its internal state.
        """
        self._initialized = False

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._reset()

    @property
    def reference(self):
        """
        Returns the current white reference object.

        :return: the white reference object
        """
        return self._reference

    @reference.setter
    def reference(self, ref):
        """
        Sets the white reference object to use.

        :param ref: the session object
        """
        self._reference = ref
        self._reset()

    def _do_initialize(self):
        """
        Hook method for initializing the white reference method.
        """
        if self._reference is None:
            raise Exception("No white reference set!")

    def _initialize(self):
        """
        Hook method for initializing the white reference method (if necessary).
        """
        if not self._initialized:
            self._do_initialize()
            self._initialized = True

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        raise NotImplementedError()

    def apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        self._initialize()
        return self._do_apply(scan)

    @classmethod
    def parse_method(cls, cmdline: str) -> 'AbstractWhiteReferenceMethod':
        """
        Splits the command-line, parses the arguments, instantiates and returns the white reference method.

        :param cmdline: the command-line to process
        :type cmdline: str
        :return: the white ref plugin
        :rtype: AbstractWhiteReferenceMethod
        """
        plugins = REGISTRY.whiteref_methods()
        args = split_args(split_cmdline(cmdline), plugins.keys())
        plugins = args_to_objects(args, plugins, allow_global_options=False)
        if len(plugins) == 1:
            return plugins[0]
        else:
            raise Exception("Expected one white reference method plugin, but got %d from command-line: %s" % (len(plugins), cmdline))


class AbstractFileBasedWhiteReferenceMethod(AbstractWhiteReferenceMethod, abc.ABC):
    """
    Ancestor for methods that apply a white reference to scans.
    """

    def __init__(self):
        """
        Basic initialization of the white reference method.
        """
        super().__init__()
        self._reference_file = None

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-f", "--reference_file", required=False, default=None, help="The ENVI reference file to load")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._reference_file = ns.reference_file

    def _do_initialize(self):
        """
        Hook method for initializing the white reference method.
        """
        if self._reference is None:
            if self._reference_file is not None:
                self._reference = envi.open(self._reference_file).load()
        super()._do_initialize()


class AbstractAnnotationBasedWhiteReferenceMethod(AbstractFileBasedWhiteReferenceMethod, abc.ABC):
    """
    Ancestor for methods that use an annotation rectangle.
    """

    def __init__(self):
        """
        Basic initialization of the white reference method.
        """
        super().__init__()
        self._annotation = None

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-a", "--annotation", metavar="COORD", type=int, help="The annotation rectangle (top, left, bottom, right)", required=False, nargs=4)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._annotation = ns.annotation

    @property
    def annotation(self):
        """
        Returns the current white reference annotation.

        :return: the white reference annotation tuple (top, left, bottom, right)
        :rtype: tuple
        """
        return self._annotation

    @annotation.setter
    def annotation(self, ann):
        """
        Sets the white reference annotation tuple to use.

        :param ann: the annotation tuple to use (top, left, bottom, right)
        :type ann: tuple
        """
        self._annotation = ann
        self._reset()

    def _do_initialize(self):
        """
        Hook method for initializing the white reference method.
        """
        super()._do_initialize()
        if self._annotation is None:
            raise Exception("No annotation set (top, left, bottom, right)!")
        if not isinstance(self._annotation, tuple):
            raise Exception("Annotation is not a tuple: %s" % str(type(self._annotation)))
        if not len(self._annotation) == 4:
            raise Exception("Annotation tuple has wrong length (expected 4): %d" % len(self._annotation))
