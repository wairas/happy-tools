import numpy as np


def check_ragged_data(data):
    first_shape = data[0].shape
    for i, array in enumerate(data):
        if array.shape != first_shape:
            print("Data contains arrays with different shapes.")
            print("Shape of the first array:", first_shape)
            print("Index:", i, "Shape:", array.shape)
            return False
    print("Data is consistent. All arrays have the same shape:", first_shape)
    return True


def remove_ragged_data(data, do_print_shapes=True):
    if do_print_shapes:
        print("Before removing ragged data:")
        print_shape(data)

    first_shape = data[0].shape
    consistent_data = [arr for arr in data if arr.shape[0] == first_shape[0]]

    if do_print_shapes:
        print("\nAfter removing ragged data:")
        print_shape(consistent_data)

    return np.array(consistent_data)


def print_shape(data):
    print(data.shape)
