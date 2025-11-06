import pytest

from framekit.master_scene_element import MasterScene
from framekit.scene_element import Scene


def test_scene_reuse_within_scene() -> None:
    child = Scene()
    child.duration = 1.5
    parent = Scene()
    parent.add(child)
    parent.add(child)
    assert len(parent.scenes) == 2
    first, second = parent.scenes
    assert first is child
    assert second is not child
    assert first.start_time == pytest.approx(0.0)
    assert second.start_time == pytest.approx(1.5)


def test_scene_reuse_in_master_scene() -> None:
    child = Scene()
    child.duration = 2.0
    master = MasterScene(width=640, height=360, fps=30)
    master.add(child)
    master.add(child)
    assert len(master.scenes) == 2
    first, second = master.scenes
    assert first is child
    assert second is not child
    assert first.start_time == pytest.approx(0.0)
    assert second.start_time == pytest.approx(2.0)
