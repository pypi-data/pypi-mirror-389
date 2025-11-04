from typing import List
from math import ceil

from PIL import Image


def draw_grid(images: List[Image.Image],
              cols: int,
              cell_width: int | None = None,
              border_width: int = 0):
    rows = int(ceil(len(images) / cols))

    width, height = images[0].size

    # Resize images, if cell width is specified
    if cell_width is not None:
        height = int(height * cell_width / width)
        width = cell_width
        images = [img.resize((width, height)) for img in images]

    width += border_width
    height += border_width

    grid = Image.new('RGB', size=(cols * width, rows * height))

    for i, img in enumerate(images):
        grid.paste(img, box=(i % cols * width, i // cols * height))

    return grid
