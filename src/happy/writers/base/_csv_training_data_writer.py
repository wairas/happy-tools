import csv
import numpy as np
from ._base_writer import BaseWriter


class CSVTrainingDataWriter(BaseWriter):
    def __init__(self, output_folder):
        super().__init__(output_folder)

    def write_data(self, data, filename, datatype_mapping=None):
        if "X_train" not in data or "y_train" not in data:
            raise ValueError("Data dictionary must contain 'X_train' and 'y_train' keys.")

        X_train = data["X_train"]
        Y_train = data["y_train"]

        X_header = data.get("X_header", None)
        Y_header = data.get("y_header", None)

        if X_header is None:
            X_header = [f"X_{i}" for i in range(len(X_train[0]))]

        if Y_header is None:
            if isinstance(Y_train[0], np.ndarray):
                Y_header = [f"target_{i}" for i in range(Y_train[0].shape[0])]
            else:
                Y_header = ["target"]

        sample_ids = data.get("sample_id", None)

        output_file_path = self.output_folder + "/" + filename + ".csv"

        with open(output_file_path, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)

            headers = ["sample_id"] if sample_ids is not None else []
            headers += X_header + Y_header
            csvwriter.writerow(headers)

            for idx, (x, y) in enumerate(zip(X_train, Y_train)):
                x_values = x.tolist()

                if isinstance(y, np.ndarray):
                    y_values = y.tolist()
                else:
                    y_values = [y]

                row = [sample_ids[idx]] if sample_ids is not None else []
                row += x_values + y_values

                csvwriter.writerow(row)

        self.logger().info(f"CSV file '{filename}.csv' written to '{self.output_folder}'.")
