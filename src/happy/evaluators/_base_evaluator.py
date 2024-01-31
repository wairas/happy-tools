from happy.base.core import ObjectWithLogging
from happy.splitters import DataSplits


class BaseEvaluator(ObjectWithLogging):

    def __init__(self, splits: DataSplits, model, target):
        super().__init__()
        self.data_splits = splits
        self.model = model
        self.target = target
        self.all_predictions = []
        self.all_actuals = []

    def evaluate(self):
        for repeat_idx, repeat_data in enumerate(self.data_splits.splits):
            for fold_idx, fold_data in enumerate(repeat_data['repeats']):
                train_ids = fold_data['train']
                test_ids = fold_data['test']
                self.model.fit(train_ids)
                predictions, actuals = self.model.predict(id_list=test_ids, return_actuals=True)
                self.accumulate_stats(predictions, actuals, repeat_idx, fold_idx )

        self.calculate_and_show_metrics()

    def calculate_and_show_metrics(self):
        # Implement this method to accumulate prediction and actuals for stats calculation
        pass

    def accumulate_stats(self, predictions, actuals, repeat: int, fold: int):
        # Implement this method to accumulate prediction and actuals for stats calculation
        pass

    def calculate_fold_metrics(self):
        # Implement this method to calculate metrics for a single fold
        pass

    def calculate_repeat_metrics(self, fold_metrics):
        # Implement this method to calculate metrics across folds for a repeat
        pass

    def display_results(self, repeat_metrics):
        # Implement this method to display evaluation results
        pass
