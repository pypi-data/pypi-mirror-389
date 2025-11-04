from typing import List, Tuple

from PIL import Image, ImageFont, ImageDraw

from .text_utils import wrap_texts, compute_texts_sizes, compute_line_spacing


def draw_x_labels(labels: List[str],
                  width: int,
                  margin: int,
                  font: ImageFont,
                  color: Tuple[int, int, int] | str | None = None) -> Image.Image:
    assert len(labels) > 0, 'At least one label must be provided'

    if color is None:
        color = 'black'

    cols = len(labels)
    cell_width = width // cols

    labels = wrap_texts(labels, font, line_length=cell_width - margin * 2)

    sizes = compute_texts_sizes(labels, font)

    line_spacing = compute_line_spacing(font)
    height = max([s[1] for s in sizes]) + line_spacing * 2

    canvas = Image.new(mode='RGB', size=(width, height), color='white')
    draw = ImageDraw.Draw(canvas)

    for i, label in enumerate(labels):
        x = cell_width * i + cell_width / 2
        y = height / 2

        draw.multiline_text(
            (x, y),
            label,
            font=font,
            fill=color,
            anchor='mm',
            align='center'
        )

    return canvas


def draw_y_labels(labels: List[str],
                  height: int,
                  margin: int,
                  font: ImageFont,
                  color: Tuple[int, int, int] | str | None = None) -> Image.Image:
    assert len(labels) > 0, 'At least one label must be provided'

    if color is None:
        color = 'black'

    rows = len(labels)
    cell_height = height // rows

    max_label_width = max([s[0] for s in compute_texts_sizes(labels, font)]) + margin * 2
    max_width = int(cell_height * 0.75)
    width = min(max_label_width, max_width)

    labels = wrap_texts(labels, font, line_length=width - margin * 2)

    sizes = compute_texts_sizes(labels, font)

    canvas = Image.new(mode='RGB', size=(width, height), color='white')
    draw = ImageDraw.Draw(canvas)

    for i, label in enumerate(labels):
        x = max(width / 2, sizes[i][0] / 2)
        y = cell_height * i + cell_height / 2

        draw.multiline_text(
            (x, y),
            label,
            font=font,
            fill=color,
            anchor='mm',
            align='center'
        )

    return canvas
