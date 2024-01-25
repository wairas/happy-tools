from logging import Logger
from typing import Optional, Dict
import numpy as np


def pad_array(array: np.ndarray, target_height: int, target_width: int, pad_value: int = 0, logger: Optional[Logger] = None):
    current_height, current_width = array.shape[:2]

    if current_height >= target_height and current_width >= target_width:
        # Array is already larger than or equal to the target size, return as is
        if logger is not None:
            logger.info(f"Current dimensions: {current_height}x{current_width}, Target dimensions: {target_height}x{target_width}")
            logger.info("No padding needed.")
        return array

    # Calculate the padding amounts
    pad_height = max(target_height - current_height, 0)
    pad_width = max(target_width - current_width, 0)

    # Calculate padding for each dimension
    padding = [(0, pad_height), (0, pad_width)]
    for _ in range(array.ndim - 2):
        padding.append((0, 0))

    # Create a new array with the desired target size
    if logger is not None:
        logger.info(f"Padding array with pad_height: {pad_height}, pad_width: {pad_width}")
    padded_array = np.pad(array, padding, mode='constant', constant_values=pad_value)

    return padded_array
