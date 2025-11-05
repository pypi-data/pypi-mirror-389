
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Tuple

import freetype
import numpy as np
from PIL import Image, ImageFilter

from .frame_base import FrameBase


class TextElement(FrameBase):
    def __init__(self, text: str, size: int = 50, color: Tuple[int, int, int] = (255, 255, 255), font_path: Optional[str] = None, bold: bool = False, quality_scale: int = 1) -> None:
        super().__init__()
        assets_font = Path(__file__).resolve().parent.parent / 'assets' / 'NotoSansJP-ExtraBold.ttf'
        self.text = text
        self.size = size
        self.color = color
        self.font_path = str(Path(font_path).resolve()) if font_path else str(assets_font)
        self.bold = bold
        self.quality_scale = max(1, quality_scale)
        self.alignment: Literal['left', 'center', 'right'] = 'left'
        self.line_spacing: int = 4
        self.outline_color: Optional[Tuple[int, int, int]] = None
        self.outline_width: int = 0
        self._face = freetype.Face(self.font_path)
        self._render_cache_key: Optional[Tuple[object, ...]] = None
        self._render_cache_image: Optional[Image.Image] = None

    def set_alignment(self, alignment: Literal['left', 'center', 'right']) -> 'TextElement':
        self.alignment = alignment
        return self

    def set_line_spacing(self, spacing: int) -> 'TextElement':
        self.line_spacing = max(spacing, 0)
        return self

    def set_outline(self, color: Tuple[int, int, int], width: int) -> 'TextElement':
        self.outline_color = color
        self.outline_width = max(width, 0)
        return self

    def set_size(self, size: int) -> 'TextElement':
        self.size = max(size, 1)
        return self

    def set_color(self, color: Tuple[int, int, int]) -> 'TextElement':
        self.color = color
        return self

    def set_font(self, font_path: str) -> 'TextElement':
        resolved = Path(font_path).resolve()
        self.font_path = str(resolved)
        self._face = freetype.Face(self.font_path)
        return self

    def set_bold(self, bold: bool) -> 'TextElement':
        self.bold = bold
        return self

    def set_quality(self, quality_scale: int) -> 'TextElement':
        self.quality_scale = max(quality_scale, 1)
        return self

    def _measure_lines(self, lines: list[str]) -> Tuple[int, int, int, int]:
        face = self._face
        face.set_char_size(self.size * self.quality_scale * 64)
        ascender = face.size.ascender >> 6
        descender = face.size.descender >> 6
        line_height = max(ascender - descender, self.size)
        widths: list[int] = []
        for line in lines:
            pen_x = 0
            for char in line:
                face.load_char(char)
                pen_x += face.glyph.advance.x >> 6
            widths.append(pen_x)
        max_width = max(widths or [1])
        total_height = len(lines) * line_height + max(0, len(lines) - 1) * self.line_spacing
        return max_width, total_height, ascender, line_height

    def _rasterize(self, lines: list[str], width: int, height: int, ascender: int, line_height: int) -> np.ndarray:
        face = self._face
        canvas_width = width + self.outline_width * 2 + self.padding['left'] + self.padding['right']
        canvas_height = height + self.outline_width * 2 + self.padding['top'] + self.padding['bottom']
        canvas = np.zeros((canvas_height, canvas_width), dtype=np.uint8)
        pen_y = self.padding['top'] + self.outline_width
        for line in lines:
            if self.alignment == 'center':
                cursor_x = self.padding['left'] + self.outline_width + (width - self._line_width(line)) // 2
            elif self.alignment == 'right':
                cursor_x = self.padding['left'] + self.outline_width + (width - self._line_width(line))
            else:
                cursor_x = self.padding['left'] + self.outline_width
            baseline = pen_y + ascender
            for char in line:
                face.load_char(char)
                glyph = face.glyph
                bitmap = glyph.bitmap
                if bitmap.width == 0 or bitmap.rows == 0:
                    cursor_x += glyph.advance.x >> 6
                    continue
                bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape((bitmap.rows, bitmap.width))
                x = cursor_x + glyph.bitmap_left
                y = baseline - glyph.bitmap_top
                x0 = max(0, x)
                y0 = max(0, y)
                x1 = min(canvas_width, x + bitmap.width)
                y1 = min(canvas_height, y + bitmap.rows)
                if x0 >= x1 or y0 >= y1:
                    cursor_x += glyph.advance.x >> 6
                    continue
                canvas_slice = canvas[y0:y1, x0:x1]
                glyph_slice = bitmap_array[y0 - y:y1 - y, x0 - x:x1 - x]
                np.maximum(canvas_slice, glyph_slice, out=canvas_slice)
                cursor_x += glyph.advance.x >> 6
            pen_y += line_height + self.line_spacing
        return canvas

    def _line_width(self, line: str) -> int:
        width = 0
        self._face.set_char_size(self.size * self.quality_scale * 64)
        for char in line:
            self._face.load_char(char)
            width += self._face.glyph.advance.x >> 6
        return width

    def render(self, time: float) -> Optional[Image.Image]:
        if not self.is_visible(time):
            return None
        key = (
            self.text,
            self.size,
            self.color,
            self.font_path,
            self.bold,
            self.quality_scale,
            self.alignment,
            self.line_spacing,
            self.outline_color,
            self.outline_width,
            self.padding['left'],
            self.padding['right'],
            self.padding['top'],
            self.padding['bottom'],
            self.background_color,
            self.background_alpha,
        )
        if key == self._render_cache_key and self._render_cache_image is not None:
            return self._render_cache_image
        lines = self.text.split('\n') or ['']
        measured_width, measured_height, ascender, line_height = self._measure_lines(lines)
        mask_array = self._rasterize(lines, measured_width, measured_height, ascender, line_height)
        mask_image = Image.fromarray(mask_array, mode='L')
        if self.outline_width > 0:
            outline_mask = mask_image.filter(ImageFilter.MaxFilter(self.outline_width * 2 + 1))
            outline_fill = Image.new('RGBA', mask_image.size, (*(self.outline_color or (0, 0, 0)), 255))
            outlined = Image.new('RGBA', mask_image.size, (0, 0, 0, 0))
            outlined.paste(outline_fill, mask=outline_mask)
        else:
            outlined = Image.new('RGBA', mask_image.size, (0, 0, 0, 0))
        text_fill = Image.new('RGBA', mask_image.size, (*self.color, 255))
        outlined.paste(text_fill, mask=mask_image)
        if self.background_color:
            background = Image.new('RGBA', mask_image.size, (*self.background_color, self.background_alpha))
            result = Image.alpha_composite(background, outlined)
        else:
            result = outlined
        self._render_cache_key = key
        self._render_cache_image = result
        return result
