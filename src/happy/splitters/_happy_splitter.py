import os
import json
import random
import argparse
from sklearn.model_selection import train_test_split


class HappySplitter:
    def __init__(self, happy_base_folder):
        self.happy_base_folder = happy_base_folder
        self.splits = []
        self.holdout_ids = []
        
    @staticmethod
    def load_splits_from_json(json_file):
        with open(json_file, 'r') as f:
            split_data = json.load(f)
        
        splitter = HappySplitter(split_data["happy_base_folder"])
        splitter.splits = split_data["splits"]
        splitter.holdout_ids = split_data["holdout_ids"]
        return splitter
        
    def get_holdout_ids(self):
        return self.holdout_ids
        
    def get_train_validation_test_splits(self, repeat_idx, fold_idx):
        if repeat_idx >= len(self.splits) or fold_idx >= len(self.splits[repeat_idx]['repeats']):
            raise ValueError("Invalid repeat or fold index.")
        
        # Get the train, validation, and test sets for the specified repeat and fold
        repeat_data = self.splits[repeat_idx]['repeats'][fold_idx]
        train_ids = repeat_data['train']
        validation_ids = repeat_data['validation']
        test_ids = repeat_data['test']
        
        return train_ids, validation_ids, test_ids

    def save_splits_to_json(self, json_file):
        split_data = {"happy_base_folder": self.happy_base_folder, "splits": self.splits, "holdout_ids": self.holdout_ids}
        with open(json_file, "w") as f:
            json.dump(split_data, f, indent=4)

    def _get_all_sample_ids(self, use_regions):
        all_sample_ids = []

        if use_regions:
            for sample_id in os.listdir(self.happy_base_folder):
                sample_path = os.path.join(self.happy_base_folder, sample_id)
                if os.path.isdir(sample_path):
                    for region in os.listdir(sample_path):
                        region_path = os.path.join(sample_path, region)
                        if os.path.isdir(region_path):
                            all_sample_ids.append(f"{sample_id}:{region}")
        else:
            for entry in os.listdir(self.happy_base_folder):
                entry_path = os.path.join(self.happy_base_folder, entry)
                if os.path.isdir(entry_path):
                    all_sample_ids.append(entry)

        return all_sample_ids

    def generate_splits(self, num_repeats, num_folds, train_percent, validation_percent, use_regions, holdout_percent=None):
        all_sample_ids = self._get_all_sample_ids(use_regions)

        # Calculate the number of examples to hold out
        if holdout_percent:
            num_holdout = int(len(all_sample_ids) * holdout_percent / 100)
            self.holdout_ids = random.sample(all_sample_ids, num_holdout)
            all_sample_ids = list(set(all_sample_ids) - set(self.holdout_ids))
        else:
            self.holdout_ids = []

        if num_folds == 1:
            # Special case: no cross-validation, directly split based on percentages
            train_ids, test_ids = train_test_split(all_sample_ids, test_size=1 - train_percent / 100, shuffle=True)

            num_train_samples = int(len(train_ids) * train_percent / 100)
            num_validation_samples = int(len(train_ids) * validation_percent / 100)
            if num_validation_samples > 0:
                train_ids, validation_ids = train_test_split(train_ids, train_size=num_train_samples, test_size=num_validation_samples, shuffle=True)
            else:
                validation_ids = []
            self.splits.append({"repeats": [{
                "train": train_ids,
                "validation": validation_ids,
                "test": test_ids
            }]})
        else:
            for repeat_idx in range(num_repeats):
                random.shuffle(all_sample_ids)

                folds_data = []
                for fold_idx in range(num_folds):
                    train_ids, test_ids = train_test_split(all_sample_ids, test_size=1/num_folds, shuffle=True)

                    num_train_samples = int(len(train_ids) * train_percent / 100)
                    num_validation_samples = int(len(train_ids) * validation_percent / 100)

                    train_ids, validation_ids = train_test_split(train_ids, train_size=num_train_samples, test_size=num_validation_samples, shuffle=True)

                    folds_data.append({
                        "train": train_ids,
                        "validation": validation_ids,
                        "test": test_ids
                    })

                self.splits.append({"repeats": folds_data})
