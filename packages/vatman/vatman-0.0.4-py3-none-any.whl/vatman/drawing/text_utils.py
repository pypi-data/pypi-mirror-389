import itertools
from typing import List, Tuple, Optional

from PIL import Image, ImageFont, ImageDraw


def load_font(fontsize: int) -> ImageFont:
    # Load font
    try:
        from fonts.ttf import Roboto
        return ImageFont.truetype(Roboto, fontsize)
    except Exception:
        return ImageFont.load_default(size=fontsize)


def wrap_line(text: str, font: ImageFont, drawing: ImageDraw, line_length: int) -> List[str]:
    lines = []
    line_words = []
    for word in text.split():
        word = word.strip()
        line = ' '.join(line_words + [word])
        if drawing.textlength(line, font=font) <= line_length:
            line_words.append(word)
        else:
            lines.append(' '.join(line_words))
            line_words = [word]

    lines.append(' '.join(line_words))

    return lines


def create_aux_drawing() -> ImageDraw:
    aux_image = Image.new('RGB', (1, 1), 'white')
    return ImageDraw.Draw(aux_image)


def wrap_text(text: str,
              font: ImageFont,
              line_length: int,
              drawing: Optional[ImageDraw.Draw] = None) -> str:
    if drawing is None:
        drawing = create_aux_drawing()

    lines = text.split('\n')
    wrapped_lines = [wrap_line(line, font, drawing, line_length) for line in lines]
    wrapped_lines = list(itertools.chain(*wrapped_lines))
    wrapped_text = '\n'.join(wrapped_lines)

    return wrapped_text


def wrap_texts(texts: List[str],
               font: ImageFont,
               line_length: int) -> List[str]:
    drawing = create_aux_drawing()

    return [wrap_text(text, font, line_length, drawing) for text in texts]


def compute_text_size(text: str,
                      font: ImageFont,
                      drawing: Optional[ImageDraw.Draw] = None) -> Tuple[int, int]:
    if drawing is None:
        drawing = create_aux_drawing()

    bbox = drawing.multiline_textbbox((0, 0), text, font=font)
    size = (bbox[2] - bbox[0], bbox[3] - bbox[1])

    return size


def compute_texts_sizes(texts: List[str],
                        font: ImageFont) -> List[Tuple[int, int]]:
    drawing = create_aux_drawing()

    return [compute_text_size(text, font, drawing) for text in texts]


def compute_line_spacing(font: ImageFont) -> int:
    one_line_height = compute_text_size('m', font)[1]
    two_lines_height = compute_text_size('m\nm', font)[1]
    return two_lines_height - 2 * one_line_height


def draw_text(text: str, x: float, y: float, font: ImageFont, drawing: ImageDraw):
    drawing.multiline_text(
        (x, y),
        text,
        font=font,
        fill=(0, 0, 0),
        anchor='mm',
        align='center'
    )


__all__ = ['load_font', 'wrap_line', 'wrap_text', 'wrap_texts', 'compute_text_size', 'compute_texts_sizes', 'draw_text']
