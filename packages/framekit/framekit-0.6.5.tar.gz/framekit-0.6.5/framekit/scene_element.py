
from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple, Union

from PIL import Image

from .audio_element import AudioElement
from .frame_base import FrameBase


class Scene(FrameBase):
    @property
    def duration(self) -> float:
        if self._explicit_duration is not None:
            return self._explicit_duration
        candidates: list[float] = []
        for element in self.elements:
            if element.duration > 0.0:
                candidates.append(element.start_time + element.duration)
        for audio in self.audio:
            length = audio.total_duration()
            if length > 0.0:
                candidates.append(audio.start_time + length)
        for scene in self.scenes:
            if scene.duration > 0.0:
                candidates.append(scene.start_time + scene.duration)
        if not candidates:
            return 0.0
        return max(candidates)

    @duration.setter
    def duration(self, value: float) -> None:
        self._explicit_duration = max(value, 0.0)

    def __init__(self) -> None:
        self._explicit_duration: Optional[float] = None
        super().__init__()
        self._explicit_duration = None
        self.scenes: list['Scene'] = []
        self.elements: list[FrameBase] = []
        self.audio: list[AudioElement] = []
        self._canvas_size: tuple[int, int] = (1920, 1080)
        self._render_cache_signature: Optional[tuple[object, ...]] = None
        self._render_cache_image: Optional[Image.Image] = None
        self._scale_cache: Dict[Tuple[int, float], Image.Image] = {}

    def set_canvas(self, width: int, height: int) -> 'Scene':
        self._canvas_size = (width, height)
        for child in self.scenes:
            child.set_canvas(width, height)
        self._render_cache_signature = None
        self._render_cache_image = None
        self._scale_cache.clear()
        return self

    def add(self, element: Union[FrameBase, 'Scene', AudioElement], layer: Literal['top', 'bottom'] = 'top') -> 'Scene':
        if isinstance(element, Scene):
            element.set_canvas(*self._canvas_size)
            if layer == 'top':
                self.scenes.append(element)
            else:
                self.scenes.insert(0, element)
            pointer = 0.0
            for child in self.scenes:
                if getattr(child, '_start_time_locked', False):
                    pointer = max(pointer, child.start_time + child.duration)
                    continue
                child.start_time = pointer
                pointer += child.duration
        elif isinstance(element, AudioElement):
            if layer == 'top':
                self.audio.append(element)
            else:
                self.audio.insert(0, element)
        else:
            if layer == 'top':
                self.elements.append(element)
            else:
                self.elements.insert(0, element)
        self._render_cache_signature = None
        self._render_cache_image = None
        self._scale_cache.clear()
        return self

    def render(self, time: float, _base: float = 0.0) -> Optional[Image.Image]:
        absolute_start = _base + self.start_time
        if time < absolute_start:
            return None
        relative_time = time - absolute_start
        if self.duration > 0.0 and relative_time >= self.duration:
            return None
        signature_parts: list[object] = [self._canvas_size]
        composition: list[tuple[Image.Image, tuple[int, int]]] = []
        # ---------------------------------------------------------
        # Collect visible children and build a signature to reuse renders
        # ---------------------------------------------------------
        for scene in self.scenes:
            nested = scene.render(time, absolute_start)
            if nested is None:
                continue
            signature_parts.append(('scene', id(scene), id(nested)))
            composition.append((nested, (0, 0)))
        for element in self.elements:
            if not element.is_visible(relative_time):
                continue
            rendered = element.render(relative_time)
            if rendered is None:
                continue
            scaled = rendered
            if element.scale != 1.0:
                cache_key = (id(rendered), element.scale)
                cached = self._scale_cache.get(cache_key)
                if cached is None:
                    new_width = max(1, int(rendered.width * element.scale))
                    new_height = max(1, int(rendered.height * element.scale))
                    # ---------------------------------------------------------
                    # Resize once per unique render+scale pair to avoid per-frame Lanczos overhead
                    # ---------------------------------------------------------
                    scaled = rendered.resize((new_width, new_height), Image.BILINEAR)
                    self._scale_cache[cache_key] = scaled
                else:
                    scaled = cached
            pos_x, pos_y = element.position_for(scaled.width, scaled.height)
            signature_parts.append(('element', id(element), id(rendered), element.scale, pos_x, pos_y, scaled.size))
            composition.append((scaled, (pos_x, pos_y)))
        signature = tuple(signature_parts)
        if signature == self._render_cache_signature and self._render_cache_image is not None:
            return self._render_cache_image
        frame = Image.new('RGBA', self._canvas_size, (0, 0, 0, 0))
        for image, position in composition:
            if image.mode == 'RGBA':
                frame.paste(image, position, image)
                continue
            frame.paste(image, position)
        self._render_cache_signature = signature
        self._render_cache_image = frame
        return frame
