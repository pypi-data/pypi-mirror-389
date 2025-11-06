from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .frame_base import FrameBase


class ImageElement(FrameBase):
    def __init__(self, image_path: Union[str, Image.Image], scale: float = 1.0) -> None:
        super().__init__()
        self._path: Optional[Path] = None
        if isinstance(image_path, Image.Image):
            self._source = image_path.convert('RGBA')
        else:
            resolved = Path(image_path).expanduser().resolve()
            if not resolved.exists():
                raise FileNotFoundError(str(resolved))
            with Image.open(resolved) as loaded:
                self._source = loaded.convert('RGBA')
            self._path = resolved
        self.original_width, self.original_height = self._source.size
        self.texture_id: Optional[int] = None
        self.texture_width, self.texture_height = self._source.size
        self.set_scale(scale)
        self._source_signature: int = hash(self._source.tobytes())
        self._render_cache_key: Optional[Tuple[object, ...]] = None
        self._render_cache_image: Optional[Image.Image] = None

    def _apply_flip(self, image: Image.Image) -> Image.Image:
        if self.flip == 'horizontal':
            return ImageOps.mirror(image)
        if self.flip == 'vertical':
            return ImageOps.flip(image)
        if self.flip == 'both':
            return ImageOps.flip(ImageOps.mirror(image))
        return image

    def _apply_crop(self, image: Image.Image) -> Image.Image:
        if self.crop_width <= 0 or self.crop_height <= 0:
            return image
        target = (self.crop_width, self.crop_height)
        if self.crop_mode == 'fill':
            return ImageOps.fit(image, target, method=Image.LANCZOS)
        fitted = image.copy()
        fitted.thumbnail(target, Image.LANCZOS)
        canvas = Image.new('RGBA', target, (0, 0, 0, 0))
        offset = ((target[0] - fitted.width) // 2, (target[1] - fitted.height) // 2)
        canvas.paste(fitted, offset, fitted)
        return canvas

    def _round_mask(self, size: Tuple[int, int], radius: float) -> Image.Image:
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        return mask

    def render(self, time: float) -> Optional[Image.Image]:
        if not self.is_visible(time):
            return None
        key = (
            self._source_signature,
            self.flip,
            self.blur_strength,
            self.crop_width,
            self.crop_height,
            self.crop_mode,
            self.rotation,
            self.border_color,
            self.border_width,
            self.padding['left'],
            self.padding['right'],
            self.padding['top'],
            self.padding['bottom'],
            self.background_color,
            self.background_alpha,
            self.corner_radius,
        )
        if key == self._render_cache_key and self._render_cache_image is not None:
            return self._render_cache_image
        image = self._apply_flip(self._source.copy())
        if self.blur_strength > 0.0:
            image = image.filter(ImageFilter.GaussianBlur(self.blur_strength))
        image = self._apply_crop(image)
        if self.rotation % 360.0 != 0.0:
            image = image.rotate(self.rotation, expand=True, resample=Image.BICUBIC)
        if self.border_color and self.border_width > 0:
            border_color = (*self.border_color, 255)
            image = ImageOps.expand(image, border=self.border_width, fill=border_color)
        padding_left = self.padding['left']
        padding_top = self.padding['top']
        padding_right = self.padding['right']
        padding_bottom = self.padding['bottom']
        final_width = image.width + padding_left + padding_right
        final_height = image.height + padding_top + padding_bottom
        final_image = Image.new('RGBA', (final_width, final_height), (0, 0, 0, 0))
        if self.background_color:
            background = Image.new('RGBA', (final_width, final_height), (*self.background_color, self.background_alpha))
            final_image = Image.alpha_composite(final_image, background)
        final_image.paste(image, (padding_left, padding_top), image)
        if self.corner_radius > 0.0:
            radius = min(self.corner_radius, min(final_width, final_height) / 2.0)
            mask = self._round_mask((final_width, final_height), radius)
            final_image = Image.composite(final_image, Image.new('RGBA', (final_width, final_height), (0, 0, 0, 0)), mask)
        self._render_cache_key = key
        self._render_cache_image = final_image
        return final_image
