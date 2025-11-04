from typing import List
from math import ceil

from PIL import Image, ImageFont

from .drawing.text_utils import load_font
from .drawing.grid import draw_grid
from .drawing.captions_overlay import overlay_captions
from .drawing.labels import draw_x_labels, draw_y_labels
from .drawing.title import draw_title


class GridBuilder:
    def __init__(self,
                 images: List[Image.Image],
                 cols: int = 1,
                 cell_width: int | None = None,
                 border: int = 0):
        self.images = images
        self.cols = cols
        self.rows = int(ceil(len(images) / cols))
        self.cell_width = cell_width
        self.border = border

        self.default_font_size = 16
        default_font = self._load_font(self.default_font_size)

        self.title: str | None = None
        self.title_font = default_font
        self.title_border = 0

        self.captions: List[str] | None = None
        self.captions_font = default_font

        self.labels_x: List[str] | None = None
        self.labels_x_font = default_font

        self.labels_y: List[str] | None = None
        self.labels_y_font = default_font

        self.labels_margin = 10

    def add_border(self, width: int) -> 'GridBuilder':
        self.border = width
        return self

    def add_title(self,
                  title: str,
                  fontsize: int | None = None,
                  border: int = 0) -> 'GridBuilder':
        self.title = title
        self.title_border = border

        if fontsize is not None:
            self.default_font_size = fontsize
        else:
            fontsize = self.default_font_size

        self.title_font = self._load_font(fontsize)

        return self

    def add_captions(self,
                     captions: List[str],
                     fontsize: int | None = None) -> 'GridBuilder':
        self.captions = captions

        if fontsize is not None:
            self.default_font_size = fontsize
        else:
            fontsize = self.default_font_size

        self.captions_font = self._load_font(fontsize)

        return self

    def add_x_labels(self,
                     labels: List[str],
                     fontsize: int | None = None) -> 'GridBuilder':
        self.labels_x = labels

        if fontsize is not None:
            self.default_font_size = fontsize
        else:
            fontsize = self.default_font_size

        self.labels_x_font = self._load_font(fontsize)

        return self

    def add_y_labels(self,
                     labels: List[str],
                     fontsize: int | None = None) -> 'GridBuilder':
        self.labels_y = labels

        if fontsize is not None:
            self.default_font_size = fontsize
        else:
            fontsize = self.default_font_size

        self.labels_y_font = self._load_font(fontsize)

        return self

    def draw(self) -> Image.Image:
        grid = draw_grid(
            self.images,
            cols=self.cols,
            cell_width=self.cell_width,
            border_width=self.border
        )

        if self.captions is not None:
            grid = overlay_captions(
                grid,
                captions=self.captions,
                font=self.captions_font,
                cols=self.cols,
                rows=self.rows,
                text_color=(0, 0, 0),
                background_color=(255, 255, 255, 128)
            )

        width, height = grid.size
        grid_x = 0
        grid_y = 0

        if self.labels_x is not None:
            labels_x_patch = draw_x_labels(
                self.labels_x,
                width=grid.width,
                margin=self.labels_margin,
                font=self.labels_x_font
            )
            height += labels_x_patch.height
            grid_y += labels_x_patch.height
        else:
            labels_x_patch = None

        if self.labels_y is not None:
            labels_y_patch = draw_y_labels(
                self.labels_y,
                height=grid.height,
                margin=self.labels_margin,
                font=self.labels_y_font
            )
            width += labels_y_patch.width
            grid_x += labels_y_patch.width
        else:
            labels_y_patch = None

        if self.title is not None:
            title_patch = draw_title(
                self.title,
                width=width,
                margin=self.labels_margin,
                border=self.title_border,
                font=self.labels_x_font
            )
            height += title_patch.height
            grid_y += title_patch.height
        else:
            title_patch = None

        canvas = Image.new(mode='RGB', size=(width, height), color='white')

        if title_patch is not None:
            canvas.paste(title_patch, (0, 0))

        if labels_x_patch is not None:
            canvas.paste(labels_x_patch, (grid_x, grid_y - labels_x_patch.height))

        if labels_y_patch is not None:
            canvas.paste(labels_y_patch, (grid_x - labels_y_patch.width, grid_y))

        canvas.paste(grid, (grid_x, grid_y))

        return canvas

    def _load_font(self, size: int) -> ImageFont:
        return load_font(size)


def make_grid(images: List[Image.Image],
              cols: int = 1,
              cell_width: int | None = None,
              border: int = 0
              ) -> GridBuilder:
    return GridBuilder(images=images, cols=cols, cell_width=cell_width, border=border)


__all__ = ['GridBuilder', 'make_grid']
