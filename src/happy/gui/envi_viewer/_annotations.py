from PIL import Image, ImageDraw


ANNOTATION_MODE_POLYGONS = "Polygons"
ANNOTATION_MODE_PIXELS = "Pixels"
ANNOTATION_MODES = [
    ANNOTATION_MODE_POLYGONS,
    ANNOTATION_MODE_PIXELS,
]



def generate_color_key(palette, labels):
    """
    Generates a color key image and displays it.

    :param palette: the color palette to use (list of (r,g,b) tuples)
    :type palette: list
    :param labels: the list of label strings to output
    :type labels: list
    :return: the generated image
    :rtype: Image.Image
    """
    x = 10
    y = 10
    inc = 25
    h = 20
    w = 100
    result = Image.new("RGBA", (400, (len(labels) + 1) * inc), "#ffffff")
    draw = ImageDraw.Draw(result)
    for i, label in enumerate(labels):
        draw.rectangle((x, y, x + w, y + h), fill=palette[i])
        draw.text((x + w + 2*x, y + 5), label, fill="#000000")
        y += inc
    return result
