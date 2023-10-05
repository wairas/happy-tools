from happy.evaluators import BaseEvaluator
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


class ClassificationEvaluator(BaseEvaluator):
    def __init__(self, happy_splitter, model, target):
        super().__init__(happy_splitter, model, target)
        self.data = {}
        
    def accumulate_stats(self, predictions, actuals, repeat, fold):
        print(f"added {repeat}:{fold}")
        if repeat not in self.data:
            self.data[repeat] = {}
        if fold not in self.data[repeat]:
            self.data[repeat][fold] = {'predictions': [], 'actuals': []}
        
        self.data[repeat][fold]['predictions'].append(predictions)
        self.data[repeat][fold]['actuals'].append(actuals)

    def calculate_and_show_metrics(self):
        all_metrics = {'accuracy': [], 'precision': [], 'recall': [], 'f1': []}
        
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
            
            combined_predictions = np.argmax(combined_fold_predictions, axis=-1)
            combined_actuals = np.argmax(combined_fold_actuals, axis=-1)
            
            accuracy = accuracy_score(combined_actuals.flatten(), combined_predictions.flatten())
            precision = precision_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            recall = recall_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            f1 = f1_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            
            all_metrics['accuracy'].append(accuracy)
            all_metrics['precision'].append(precision)
            all_metrics['recall'].append(recall)
            all_metrics['f1'].append(f1)
            
            confusion = confusion_matrix(combined_actuals.flatten(), combined_predictions.flatten())
            
            print(f"Metrics for Repeat: {repeat}, Combined Folds:")
            print("Accuracy:", accuracy)
            print("Precision:", precision)
            print("Recall:", recall)
            print("F1 Score:", f1)
            print("Confusion Matrix:\n", confusion)
            print("=" * 50)
        
        # Calculate and print averages and standard deviations across repeats
        avg_accuracy = np.mean(all_metrics['accuracy'])
        std_accuracy = np.std(all_metrics['accuracy'])
        avg_precision = np.mean(all_metrics['precision'])
        std_precision = np.std(all_metrics['precision'])
        avg_recall = np.mean(all_metrics['recall'])
        std_recall = np.std(all_metrics['recall'])
        avg_f1 = np.mean(all_metrics['f1'])
        std_f1 = np.std(all_metrics['f1'])
        
        print("Average Accuracy across Repeats:", avg_accuracy)
        print("Standard Deviation Accuracy across Repeats:", std_accuracy)
        print("Average Precision across Repeats:", avg_precision)
        print("Standard Deviation Precision across Repeats:", std_precision)
        print("Average Recall across Repeats:", avg_recall)
        print("Standard Deviation Recall across Repeats:", std_recall)
        print("Average F1 Score across Repeats:", avg_f1)
        print("Standard Deviation F1 Score across Repeats:", std_f1)

    """
    def calculate_and_show_metrics(self):
        all_metrics = {'accuracy': [], 'precision': [], 'recall': [], 'f1': []}
        
        for repeat, fold_data in self.data.items():
            print(f"repeat: {repeat}")
            all_combined_predictions = []
            all_combined_actuals = []
            
            for fold, fold_info in fold_data.items():
                fold_predictions = np.concatenate(fold_info['predictions'])
                fold_actuals = np.concatenate(fold_info['actuals'])
                
                all_combined_predictions.append(fold_predictions)
                all_combined_actuals.append(fold_actuals)
            
            combined_predictions = np.stack(all_combined_predictions)
            combined_actuals = np.stack(all_combined_actuals)
            
            combined_predictions = np.argmax(combined_predictions, axis=-1)
            combined_actuals = np.argmax(combined_actuals, axis=-1)
            
            accuracy = accuracy_score(combined_actuals.flatten(), combined_predictions.flatten())
            precision = precision_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            recall = recall_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            f1 = f1_score(combined_actuals.flatten(), combined_predictions.flatten(), average='macro')
            
            all_metrics['accuracy'].append(accuracy)
            all_metrics['precision'].append(precision)
            all_metrics['recall'].append(recall)
            all_metrics['f1'].append(f1)
            
            confusion = confusion_matrix(combined_actuals.flatten(), combined_predictions.flatten())
            
            print(f"Metrics for Repeat: {repeat}")
            print("Accuracy:", accuracy)
            print("Precision:", precision)
            print("Recall:", recall)
            print("F1 Score:", f1)
            print("Confusion Matrix:\n", confusion)
            print("=" * 50)
        
        avg_accuracy = np.mean(all_metrics['accuracy'])
        std_accuracy = np.std(all_metrics['accuracy'])
        avg_precision = np.mean(all_metrics['precision'])
        std_precision = np.std(all_metrics['precision'])
        avg_recall = np.mean(all_metrics['recall'])
        std_recall = np.std(all_metrics['recall'])
        avg_f1 = np.mean(all_metrics['f1'])
        std_f1 = np.std(all_metrics['f1'])
        
        print("Average Accuracy across Repeats:", avg_accuracy)
        print("Standard Deviation Accuracy across Repeats:", std_accuracy)
        print("Average Precision across Repeats:", avg_precision)
        print("Standard Deviation Precision across Repeats:", std_precision)
        print("Average Recall across Repeats:", avg_recall)
        print("Standard Deviation Recall across Repeats:", std_recall)
        print("Average F1 Score across Repeats:", avg_f1)
        print("Standard Deviation F1 Score across Repeats:", std_f1)
    """