import abc
import os
import random
from typing import List, Optional, Tuple, Dict

from happy.base.core import ObjectWithLogging
from ._data_splits import DataSplits


class BaseSplitter(ObjectWithLogging, abc.ABC):
    """
    Ancestor for splitter classes that generate data splits for datasets.
    """

    def __init__(self, base_folder: str, use_regions: bool, holdout_percent: Optional[float] = None, seed: Optional[int] = None):
        """
        Initializes the splitter.

        :param base_folder: the folder to use
        :type base_folder: str
        :param use_regions: whether to use the regions
        :type use_regions: bool
        :param holdout_percent: the percentage to use for the holdout set, ignored if None
        :type holdout_percent: float
        :param seed: the seed to use for the random number generator, unseeded if None
        :type: seed
        """
        super().__init__()
        self.base_folder = base_folder
        self.use_regions = use_regions
        self.holdout_percent = holdout_percent
        self.seed: int = seed
        self.rng: Optional[random.Random] = None

    def _initialize(self):
        """
        Initializes member variables.
        """
        if self.rng is None:
            self.rng = random.Random(self.seed)

    def _next_randint(self) -> int:
        """
        Returns the next random integer from the random number generator.

        :return: the random integer
        :rtype: int
        """
        if self.rng is None:
            self._initialize()
        return self.rng.randint(0, 100)

    def _get_all_sample_ids(self) -> List[str]:
        """
        Locates all the sample IDs in the base folder.

        :return: the list of sample IDs
        :rtype: list
        """
        all_sample_ids = []

        if self.use_regions:
            for sample_id in os.listdir(self.base_folder):
                sample_path = os.path.join(self.base_folder, sample_id)
                if os.path.isdir(sample_path):
                    for region in os.listdir(sample_path):
                        region_path = os.path.join(sample_path, region)
                        if os.path.isdir(region_path):
                            all_sample_ids.append(f"{sample_id}:{region}")
        else:
            for entry in os.listdir(self.base_folder):
                entry_path = os.path.join(self.base_folder, entry)
                if os.path.isdir(entry_path):
                    all_sample_ids.append(entry)

        all_sample_ids.sort()

        return all_sample_ids

    def _split_off_holdout_set(self, all_sample_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Splits off the holdout set from all the sample IDs.

        :param all_sample_ids: the sample IDs to split off the holdout set
        :type all_sample_ids: list
        :return: the tuple of the remaining sample IDs (list) and the holdout set (list)
        """
        # Calculate the number of examples to hold out
        if self.holdout_percent is not None:
            num_holdout = int(len(all_sample_ids) * self.holdout_percent / 100)
            holdout_ids = self.rng.sample(all_sample_ids, num_holdout)
            all_sample_ids = list(set(all_sample_ids) - set(holdout_ids))
        else:
            holdout_ids = []
        return all_sample_ids, holdout_ids

    def _do_generate_splits(self, all_sample_ids: List[str]) -> List[Dict[str, List[Dict[str, List[str]]]]]:
        """
        Generates the splits.

        :param all_sample_ids: the sample IDs to split
        :type all_sample_ids: list
        :return: the generated splits
        :rtype: DataSplits
        """
        raise NotImplementedError()

    def generate_splits(self) -> DataSplits:
        """
        Generates the splits.

        :return: the generated splits
        :rtype: DataSplits
        """
        self._initialize()
        all_sample_ids = self._get_all_sample_ids()
        all_sample_ids, holdout_ids = self._split_off_holdout_set(all_sample_ids)
        splits = self._do_generate_splits(all_sample_ids)
        return DataSplits(self.base_folder, splits, holdout_ids)
