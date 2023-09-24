import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from happy.evaluators.base_evaluator import BaseEvaluator


class RegressionEvaluator(BaseEvaluator):
    def __init__(self, happy_splitter, model, target):
        super().__init__(happy_splitter, model, target)
        self.data = {}
        
    """
    def accumulate_stats(self, predictions, actuals, repeat, fold):
        print(f"added {repeat}:{fold}")
        if repeat not in self.data:
            self.data[repeat] = {}
        if fold not in self.data[repeat]:
            self.data[repeat][fold] = {'predictions': [], 'actuals': []}
        
        self.data[repeat][fold]['predictions'].append(predictions)
        self.data[repeat][fold]['actuals'].append(actuals)
        # print(self.data)
    """

    def accumulate_stats(self, predictions, actuals, repeat, fold, ignore_value=-1):
        print(f"added {repeat}:{fold}")
        if repeat not in self.data:
            self.data[repeat] = {}
        if fold not in self.data[repeat]:
            self.data[repeat][fold] = {'predictions': [], 'actuals': []}

        # Filter out the ignore_value from predictions and actuals
        valid_indices = actuals != ignore_value
        valid_predictions = predictions[valid_indices]
        valid_actuals = actuals[valid_indices]

        self.data[repeat][fold]['predictions'].append(valid_predictions)
        self.data[repeat][fold]['actuals'].append(valid_actuals)
        
    def calculate_and_show_metrics(self):
        all_metrics = {'mean_squared_error': [], 'mean_absolute_error': [], 'bias': [], 'rmse': [], 'r2': []}
        
        for repeat, fold_data in self.data.items():
            print(f"repeat: {repeat}")
            combined_fold_predictions = []
            combined_fold_actuals = []
            
            for fold, fold_info in fold_data.items():
                fold_predictions = np.concatenate(fold_info['predictions'])
                fold_actuals = np.concatenate(fold_info['actuals'])
                
                combined_fold_predictions.append(fold_predictions)
                combined_fold_actuals.append(fold_actuals)
            
            combined_fold_predictions = np.concatenate(combined_fold_predictions)
            combined_fold_actuals = np.concatenate(combined_fold_actuals)
            
            mse = mean_squared_error(combined_fold_actuals.flatten(), combined_fold_predictions.flatten())
            mae = mean_absolute_error(combined_fold_actuals.flatten(), combined_fold_predictions.flatten())
            bias = np.mean(combined_fold_predictions.flatten() - combined_fold_actuals.flatten())
            rmse = np.sqrt(mse)
            r2 = r2_score(combined_fold_actuals.flatten(), combined_fold_predictions.flatten())
            
            all_metrics['mean_squared_error'].append(mse)
            all_metrics['mean_absolute_error'].append(mae)
            all_metrics['bias'].append(bias)
            all_metrics['rmse'].append(rmse)
            all_metrics['r2'].append(r2)
            
            print(f"Metrics for Repeat: {repeat}, Combined Folds:")
            print("Mean Squared Error:", mse)
            print("Mean Absolute Error:", mae)
            print("Bias:", bias)
            print("Root Mean Squared Error:", rmse)
            print("R-squared:", r2)
            print("=" * 50)
        
        # Calculate and print averages and standard deviations across repeats
        avg_mse = np.mean(all_metrics['mean_squared_error'])
        std_mse = np.std(all_metrics['mean_squared_error'])
        avg_mae = np.mean(all_metrics['mean_absolute_error'])
        std_mae = np.std(all_metrics['mean_absolute_error'])
        avg_bias = np.mean(all_metrics['bias'])
        std_bias = np.std(all_metrics['bias'])
        avg_rmse = np.mean(all_metrics['rmse'])
        std_rmse = np.std(all_metrics['rmse'])
        avg_r2 = np.mean(all_metrics['r2'])
        std_r2 = np.std(all_metrics['r2'])
        
        print("Average Mean Squared Error across Repeats:", avg_mse)
        print("Standard Deviation Mean Squared Error across Repeats:", std_mse)
        print("Average Mean Absolute Error across Repeats:", avg_mae)
        print("Standard Deviation Mean Absolute Error across Repeats:", std_mae)
        print("Average Bias across Repeats:", avg_bias)
        print("Standard Deviation Bias across Repeats:", std_bias)
        print("Average Root Mean Squared Error across Repeats:", avg_rmse)
        print("Standard Deviation Root Mean Squared Error across Repeats:", std_rmse)
        print("Average R-squared across Repeats:", avg_r2)
        print("Standard Deviation R-squared across Repeats:", std_r2)
