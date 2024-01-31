import json

from typing import List, Tuple, Dict


class DataSplits:
    """
    Container for data splits.
    """

    def __init__(self, base_folder: str, splits: List[Dict[str, List[Dict[str, List[str]]]]], holdout_ids: List[str]):
        """
        Initializes the splits.

        :param base_folder: the base folder
        :type base_folder: str
        :param splits: the splits data
        :type splits: list
        :param holdout_ids: the list of IDs of the holdout set
        :type holdout_ids: list
        """
        self.base_folder = base_folder
        self.splits = splits
        self.holdout_ids = holdout_ids

    def get_holdout_ids(self) -> List[str]:
        """
        Returns the holdout set IDs.

        :return: the IDs
        :rtype: list
        """
        return self.holdout_ids

    def get_train_validation_test_splits(self, repeat: int, fold: int) -> Tuple[List[str], List[str], List[str]]:
        """
        Returns the splits for the specified repeat/fold.

        :param repeat: the repeat to retrieve
        :type repeat: int
        :param fold: the fold to retrieve
        :type fold: int
        :return: the splits, tuple of train/val/test ID lists
        :rtype: tuple
        """
        if repeat >= len(self.splits) or fold >= len(self.splits[repeat]['repeats']):
            raise ValueError("Invalid repeat or fold index: repeat=%d, fold=%d" % (repeat, fold))

        # Get the train, validation, and test sets for the specified repeat and fold
        repeat_data = self.splits[repeat]['repeats'][fold]
        train_ids = repeat_data['train']
        val_ids = repeat_data['validation']
        test_ids = repeat_data['test']

        return train_ids, val_ids, test_ids

    def save(self, path: str):
        """
        Saves the splits to a JSON file.

        :param path: the JSON file to save the splits to
        :type path: str
        """
        split_data = {
            "base_folder": self.base_folder,
            "splits": self.splits,
            "holdout_ids": self.holdout_ids
        }
        with open(path, "w") as f:
            json.dump(split_data, f, indent=4)

    @staticmethod
    def load(path: str) -> 'DataSplits':
        """
        Loads the splits from a JSON file.

        :param path: the JSON file to load the splits from
        :type path: str
        :return: the splits
        :rtype: DataSplits
        """
        with open(path, 'r') as f:
            data = json.load(f)

        # for backwards compatibility
        if "happy_base_folder" in data:
            return DataSplits(data["happy_base_folder"], data["splits"], data["holdout_ids"])
        else:
            return DataSplits(data["base_folder"], data["splits"], data["holdout_ids"])
