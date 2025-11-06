
from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple, TypeVar, Union, cast


FrameBaseT = TypeVar('FrameBaseT', bound='FrameBase')


class FrameBase:
    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self.start_time: float = 0.0
        self.duration: float = 0.0
        self.visible: bool = True
        self.position_anchor: Literal['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'] = 'top-left'
        self.background_color: Optional[Tuple[int, int, int]] = None
        self.background_alpha: int = 0
        self.padding: Dict[str, int] = {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        self.border_color: Optional[Tuple[int, int, int]] = None
        self.border_width: int = 0
        self.corner_radius: float = 0.0
        self.crop_width: int = 0
        self.crop_height: int = 0
        self.crop_mode: Literal['fill', 'fit'] = 'fill'
        self.blur_strength: float = 0.0
        self.rotation: float = 0.0
        self.scale: float = 1.0
        self.flip: Literal['horizontal', 'vertical', 'both', 'none'] = 'none'
        self._start_time_locked: bool = False

    def set_position(self: FrameBaseT, x: float, y: float, anchor: Optional[Literal['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right']] = None) -> FrameBaseT:
        self.x = x
        self.y = y
        if anchor:
            self.position_anchor = anchor
        return self

    def set_scale(self: FrameBaseT, scale: float) -> FrameBaseT:
        self.scale = max(scale, 0.0)
        return self

    def _calculate_anchor_offset(self, element_width: float, element_height: float) -> Tuple[float, float]:
        if self.position_anchor == 'center':
            return element_width / 2, element_height / 2
        if self.position_anchor == 'top-right':
            return element_width, 0.0
        if self.position_anchor == 'bottom-left':
            return 0.0, element_height
        if self.position_anchor == 'bottom-right':
            return element_width, element_height
        return 0.0, 0.0

    def position_for(self, element_width: int, element_height: int) -> Tuple[int, int]:
        offset_x, offset_y = self._calculate_anchor_offset(element_width * self.scale, element_height * self.scale)
        return int(self.x - offset_x), int(self.y - offset_y)

    def set_duration(self: FrameBaseT, duration: float) -> FrameBaseT:
        self.duration = max(duration, 0.0)
        return self

    def set_start_at(self: FrameBaseT, time: float) -> FrameBaseT:
        self.start_time = max(time, 0.0)
        self._start_time_locked = True
        return self

    def set_background(self: FrameBaseT, color: Tuple[int, int, int], alpha: int = 255, padding: Union[int, Dict[str, int]] = 5) -> FrameBaseT:
        self.background_color = color
        self.background_alpha = max(0, min(alpha, 255))
        if isinstance(padding, int):
            self.padding = {'left': padding, 'right': padding, 'top': padding, 'bottom': padding}
        else:
            self.padding.update({k: max(v, 0) for k, v in padding.items()})
        return self

    def set_border(self: FrameBaseT, color: Tuple[int, int, int], width: int = 1) -> FrameBaseT:
        self.border_color = color
        self.border_width = max(width, 0)
        return self

    def set_corner_radius(self: FrameBaseT, radius: float) -> FrameBaseT:
        self.corner_radius = max(radius, 0.0)
        return self

    def set_crop(self: FrameBaseT, width: int, height: int, mode: Literal['fill', 'fit'] = 'fill') -> FrameBaseT:
        self.crop_width = max(width, 0)
        self.crop_height = max(height, 0)
        self.crop_mode = mode
        return self

    def set_blur(self: FrameBaseT, strength: float) -> FrameBaseT:
        self.blur_strength = max(strength, 0.0)
        return self

    def set_rotate(self: FrameBaseT, angle: float) -> FrameBaseT:
        self.rotation = angle
        return self

    def set_flip(self: FrameBaseT, direction: Union[str, Literal['horizontal', 'vertical', 'both', 'none']] = 'horizontal') -> FrameBaseT:
        if direction in ('horizontal', 'vertical', 'both', 'none'):
            self.flip = cast(Literal['horizontal', 'vertical', 'both', 'none'], direction)
        return self

    def is_visible(self, time: float) -> bool:
        if not self.visible:
            return False
        if time < self.start_time:
            return False
        if self.duration == 0:
            return True
        return time < self.start_time + self.duration

    def render(self, time: float) -> None:
        raise NotImplementedError
