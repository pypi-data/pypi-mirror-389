from typing import Tuple

from PIL import Image, ImageFont, ImageDraw

from .text_utils import wrap_text, compute_text_size, compute_line_spacing


def draw_title(title: str,
               width: int,
               margin: int,
               font: ImageFont,
               border: int = 0,
               color: Tuple[int, int, int] | str | None = None) -> Image.Image:
    if color is None:
        color = 'black'

    title = wrap_text(title, font, line_length=width - margin * 2)
    title_size = compute_text_size(title, font)
    line_spacing = compute_line_spacing(font)
    height = title_size[1] + line_spacing * 2 + border

    canvas = Image.new(mode='RGB', size=(width, height), color='white')
    draw = ImageDraw.Draw(canvas)

    x = width / 2
    y = (height - border) / 2

    draw.multiline_text(
        (x, y),
        title,
        font=font,
        fill=color,
        anchor='mm',
        align='center'
    )

    if border > 0:
        x1 = 0
        x2 = width
        y = height - border
        draw.line((x1, y, x2, y), fill=color, width=border)

    return canvas
