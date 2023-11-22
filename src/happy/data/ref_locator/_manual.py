from ._core import AbstractReferenceLocator


class ManualLocator(AbstractReferenceLocator):

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "rl-manual"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Reference locator where the user has to manually locate the reference file."

    def _do_locate(self):
        """
        Attempts to locate the reference data.

        :return: the suggested reference data, None if failed to do so
        """
        return None
