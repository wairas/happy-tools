import argparse
import csv
import numpy as np

from ._core import AbstractFileBasedBlackReferenceMethod


class BlackReferenceColumnAverage(AbstractFileBasedBlackReferenceMethod):
    """
    Computes the average per band per column.
    """

    def __init__(self):
        """
        Basic initialization of the black reference method.
        """
        super().__init__()
        self._avg = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "br-col-avg"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Black reference method that computes the average per band, per column. Requires the scan and reference to have the same number of columns."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-a", "--average_file", required=False, default=None, help="CSV file for storing the averages in")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self._average_file = ns.average_file

    def _do_initialize(self):
        """
        Hook method for initializing the black reference method.
        """
        super()._do_initialize()
        num_columns = self.reference.shape[1]
        self._avg = []
        for col in range(num_columns):
            self._avg.append(np.mean(self.reference[:, col, :], axis=0))
        # output averages?
        if self._average_file is not None:
            self.logger().info("Writing averages to: %s" % self._average_file)
            row = ["col"]
            row.extend(["band-" + str(x) for x in range(self.reference.shape[2])])
            with open(self._average_file, "w") as fp:
                writer = csv.writer(fp)
                # header
                writer.writerow(row)
                # data
                for i, avg in enumerate(self._avg):
                    row = [i]
                    avg = np.squeeze(avg)
                    row.extend([float(x) for x in avg])
                    writer.writerow(row)

    def _do_apply(self, scan):
        """
        Applies the white reference to the scan and returns the updated scan.

        :param scan: the scan to apply the white reference to
        :return: the updated scan
        """
        # ensure that number of cols match
        if scan.shape[1] != self.reference.shape[1]:
            raise Exception("The number of columns in the scan differ from the black reference ones: %d != %d" % (scan.shape[1], self.reference.shape[1]))
        result = scan.copy()
        for col in range(len(self._avg)):
            result[:, col, :] -= self._avg[col]
        return result
