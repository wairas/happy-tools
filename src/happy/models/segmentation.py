import numpy as np
from matplotlib import cm
from PIL import Image


def create_prediction_image(prediction):
    # Create a grayscale prediction image
    prediction = np.argmax(prediction, axis=-1)
    prediction_image = Image.fromarray(prediction.astype(np.uint8))
    return prediction_image


def create_false_color_image(prediction, mapping):
    # Create a false color prediction image
    prediction = np.argmax(prediction, axis=-1)
    cmap = cm.get_cmap('viridis', len(mapping))
    false_color = cmap(prediction)
    false_color_image = Image.fromarray((false_color[:, :, :3] * 255).astype(np.uint8))
    return false_color_image
