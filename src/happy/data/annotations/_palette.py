import math
from matplotlib.colors import TABLEAU_COLORS, hex2color


def tableau_colors(max_colors=255, alpha=None):
    """
    Generates a palette from TABLEAU_COLORS with 255 entries.
    It iterates over the TABLEAU_COLORS several times, each
    time making the colors darker.

    :param max_colors: the maximum number of colors to generate
    :type max_colors: int
    :param alpha: the alpha value to use (None -> RGB, otherwise -> RGBA)
    :return: the palette (list of (r,g,b) or (r,g,b,a) tuples)
    :rtype: list
    """
    result = []
    num_rounds = math.ceil(max_colors / len(TABLEAU_COLORS))
    decrement_per_round = 1.0 / num_rounds
    for i in range(num_rounds):
        darken_factor = 1.0 - decrement_per_round * i
        for name in TABLEAU_COLORS:
            if len(result) == max_colors:
                break
            color = hex2color(TABLEAU_COLORS[name])
            r, g, b = [int(x * darken_factor * max_colors) for x in color]
            if alpha is None:
                result.append((r, g, b))
            else:
                result.append((r, g, b, alpha))
    return result
