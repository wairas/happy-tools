class BaseEvaluator:
    def __init__(self, happy_splitter, model, target):
        self.happy_splitter = happy_splitter
        self.model = model
        self.target = target
        self.all_predictions = []
        self.all_actuals = []

    def evaluate(self):
        for repeat_idx, repeat_data in enumerate(self.happy_splitter.splits):
            fold_metrics = []
            for fold_idx, fold_data in enumerate(repeat_data['repeats']):
                train_ids = fold_data['train']
                test_ids = fold_data['test']

                self.model.fit(train_ids)
                predictions, actuals = self.model.predict(id_list=test_ids, return_actuals=True)
                
                self.accumulate_stats(predictions, actuals, repeat_idx, fold_idx )

            #repeat_metrics = self.calculate_repeat_metrics(fold_metrics)
            #self.all_repeat_metrics.append(repeat_metrics)
            #self.all_fold_metrics.append(fold_metrics)
            
        self.calculate_and_show_metrics()

    def calculate_and_show_metrics(self):
        # Implement this method to accumulate prediction and actuals for stats calculation
        pass

    def accumulate_stats(self, predictions, actuals, repeat, fold):
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

        """
# Usage example
splitter = HappySplitter(happy_base_folder)
splitter.load_splits_from_json('split_data.json')  # Load your split data
model = HappyModel(data_folder, target)
evaluator = BaseEvaluator(splitter, model, target)
evaluator.evaluate()

# Access metrics later
all_fold_metrics = evaluator.all_fold_metrics
all_repeat_metrics = evaluator.all_repeat_metrics
"""