import copy
import json


class MetaDataManager:
    """
    Simple meta-data manager.
    """

    def __init__(self):
        self.metadata = dict()

    def __len__(self):
        """
        Returns the number of meta-data entries.

        :return: the number of entries
        :rtype: int
        """
        return len(self.metadata)

    def clear(self):
        """
        Clears the metadata.
        """
        self.metadata = dict()

    def set(self, k, v):
        """
        Sets the specified meta-data value.

        :param k: the key
        :type k: str
        :param v: the associated value
        :type v: str
        """
        self.metadata[k] = v

    def remove(self, k):
        """
        Removes the specified key from the meta-data.

        :param k: the key to remove
        :type k: str
        :return: None if successfully removed, otherwise error message
        :rtype: str
        """
        if k in self.metadata:
            self.metadata.pop(k)
        else:
            return "No meta-data value stored under '%s'!" % k

    def update(self, metadata):
        """
        Updates its meta-data dictionary with the provided one.

        :param metadata: the meta-data dictionary to use for the update
        :type metadata: dict
        """
        self.metadata.update(metadata)

    def to_dict(self):
        """
        Returns a copy of the underlying meta-data dictionary.

        :return: the meta-data
        :rtype: dict
        """
        return copy.copy(self.metadata)

    def to_json(self):
        """
        Returns itself in JSON represention.

        :return: the JSON string
        :rtype: str
        """
        return json.dumps(self.to_dict())

    def from_json(self, s):
        """
        Restores the meta-data from the provided JSON.

        :param s: the JSON string to restore from
        :type s: str
        :return: if successfully restored
        :rtype: bool
        """
        d = json.loads(s)
        if not isinstance(d, dict):
            return False
        self.clear()
        for k in d:
            self.set(k, d[k])
        return True
