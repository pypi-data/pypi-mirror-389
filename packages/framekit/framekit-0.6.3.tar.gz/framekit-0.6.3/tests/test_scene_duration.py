from __future__ import annotations

import pytest

from framekit.frame_base import FrameBase
from framekit.scene_element import Scene


class _DummyElement(FrameBase):
    def __init__(self, start: float, duration: float) -> None:
        super().__init__()
        self.set_start_at(start)
        self.set_duration(duration)

    def render(self, time: float) -> None:
        return None


def test_scene_duration_from_elements() -> None:
    scene = Scene()
    scene.add(_DummyElement(0.0, 2.0))
    scene.add(_DummyElement(2.0, 4.0))
    assert scene.duration == pytest.approx(6.0)


def test_scene_duration_with_nested_scene() -> None:
    parent = Scene()
    child = Scene()
    child.add(_DummyElement(0.0, 1.5))
    child.set_start_at(0.5)
    parent.add(child)
    assert parent.duration == pytest.approx(0.5 + child.duration)


def test_scene_duration_explicit_override() -> None:
    scene = Scene()
    scene.add(_DummyElement(0.0, 2.0))
    scene.set_duration(10.0)
    assert scene.duration == pytest.approx(10.0)
