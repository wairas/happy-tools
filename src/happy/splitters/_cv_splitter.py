from sklearn.model_selection import train_test_split
from typing import List, Optional, Dict

from ._base_splitter import BaseSplitter


class CrossValidationSplitter(BaseSplitter):
    """
    Generates cross-validation-like splits.
    """

    def __init__(self, base_folder: str, use_regions: bool, num_repeats: int, num_folds: int, train_percent: float, validation_percent: float, holdout_percent: Optional[float] = None, seed: Optional[int] = None):
        """
        Initializes the splitter.

        :param base_folder: the folder to use
        :type base_folder: str
        :param use_regions: whether to use the regions
        :type use_regions: bool
        :param num_repeats: the number of repeats to generate
        :type num_repeats: int
        :param num_folds: the number of cross-validation folds to generate
        :type num_folds: int
        :param train_percent: the percentage to use for the training set
        :type train_percent: float
        :param validation_percent: the percentage to use for the validation set
        :type validation_percent: float
        :param holdout_percent: the percentage to use for the holdout set, ignored if None
        :type holdout_percent: float
        :param seed: the seed to use for the random number generator, unseeded if None
        :type: seed
        """
        super().__init__(base_folder, use_regions, holdout_percent=holdout_percent, seed=seed)
        self.train_percent = train_percent
        self.validation_percent = validation_percent
        self.num_repeats = num_repeats
        self.num_folds = num_folds

    def _do_generate_splits(self, all_sample_ids: List[str]) -> List[Dict[str, List[Dict[str, List[str]]]]]:
        """
        Generates the splits.

        :param all_sample_ids: the sample IDs to split
        :type all_sample_ids: list
        :return: the generated splits
        :rtype: DataSplits
        """
        result = []

        for repeat_idx in range(self.num_repeats):
            self.rng.shuffle(all_sample_ids)

            folds_data = []
            for fold_idx in range(self.num_folds):
                train_ids, test_ids = train_test_split(
                    all_sample_ids,
                    test_size=1 / self.num_folds,
                    shuffle=True,
                    random_state=self._next_randint())

                num_train_samples = int(len(train_ids) * self.train_percent / 100)
                num_validation_samples = int(len(train_ids) * self.validation_percent / 100)

                train_ids, validation_ids = train_test_split(
                    train_ids,
                    train_size=num_train_samples,
                    test_size=num_validation_samples,
                    shuffle=True,
                    random_state=self._next_randint())

                folds_data.append({
                    "train": train_ids,
                    "validation": validation_ids,
                    "test": test_ids
                })

            result.append({"repeats": folds_data})

        return result
