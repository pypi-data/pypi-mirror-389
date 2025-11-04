from typing import List, Tuple

from PIL import Image, ImageFont, ImageDraw

from .text_utils import *


def overlay_captions(grid: Image.Image,
                     captions: List[str],
                     font: ImageFont,
                     cols: int,
                     rows: int,
                     text_color: Tuple | None = None,
                     background_color: Tuple | None = None
                     ) -> Image.Image:
    if text_color is None:
        text_color = (0, 0, 0)

    width, height = grid.size
    cell_width = width // cols
    cell_height = height // rows

    captions = wrap_texts(captions, font, line_length=int(cell_width * 0.95))
    caption_sizes = compute_texts_sizes(captions, font)

    caption_sizes = normalize_caption_sizes(caption_sizes)

    overlay = Image.new(size=grid.size, mode='RGBA')
    drawing = ImageDraw.Draw(overlay)

    if background_color is not None:
        for i, caption_size in enumerate(caption_sizes):
            row = i // cols
            col = i % cols

            x0 = cell_width * col
            y0 = cell_height * row
            x1 = x0 + cell_width
            y1 = y0 + caption_size[1]
            drawing.rectangle((x0, y0, x1, y1), fill=background_color)

    for i, (caption, caption_size) in enumerate(zip(captions, caption_sizes)):
        row = i // cols
        col = i % cols
        x = cell_width * col + cell_width / 2
        y = cell_height * row + caption_size[1] / 2
        drawing.multiline_text(
            (x, y),
            caption,
            font=font,
            fill=text_color,
            anchor='mm',
            align='center'
        )

    input_mode = grid.mode
    if input_mode != 'RGBA':
        grid = grid.convert('RGBA')

    result = Image.alpha_composite(grid, overlay)

    if result.mode != input_mode:
        result = result.convert(input_mode)

    return result


def normalize_caption_sizes(sizes: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    # Normalize caption heights
    max_text_height = max([s[1] for s in sizes])
    max_text_height = int(max_text_height * 1.5)
    return [(s[0], max_text_height) for s in sizes]
