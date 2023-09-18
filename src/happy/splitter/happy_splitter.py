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
        return(self.holdout_ids)
        
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
            all_sample_ids = [f"{sample_id}:{region}" for sample_id in os.listdir(self.happy_base_folder) for region in os.listdir(os.path.join(self.happy_base_folder, sample_id))]
        else:
            all_sample_ids = os.listdir(self.happy_base_folder)
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

            train_ids, validation_ids = train_test_split(train_ids, train_size=num_train_samples, test_size=num_validation_samples, shuffle=True)

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
           
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate train/validation/test splits for Happy data.')
    parser.add_argument('happy_base_folder', type=str, help='Path to the Happy base folder')
    parser.add_argument('--num_repeats', type=int, default=1, help='Number of repeats')
    parser.add_argument('--num_folds', type=int, default=1, help='Number of folds')
    parser.add_argument('--train_percent', type=float, default=70.0, help='Percentage of data in the training set')
    parser.add_argument('--validation_percent', type=float, default=10.0, help='Percentage of data in the validation set')
    parser.add_argument('--use_regions', action='store_true', help='Use regions in generating splits')
    parser.add_argument('--holdout_percent', type=float, default=None, help='Percentage of data to hold out as a holdout set')
    parser.add_argument('--output_file', type=str, default='output_split.json', help='Path to the output split file')
    args = parser.parse_args()

    splitter = HappySplitter(args.happy_base_folder)
    splitter.generate_splits(args.num_repeats, args.num_folds, args.train_percent, args.validation_percent, args.use_regions, args.holdout_percent)

    # Save splits in the correct format
    splitter.save_splits_to_json(args.output_file)