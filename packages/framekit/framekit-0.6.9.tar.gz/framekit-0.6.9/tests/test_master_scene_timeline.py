import pytest

from framekit.master_scene_element import MasterScene
from framekit.scene_element import Scene


def test_master_add_assigns_sequential_start_times() -> None:
    master = MasterScene()
    scene1 = Scene()
    scene1.duration = 5.0
    scene2 = Scene()
    scene2.duration = 3.0
    master.add(scene1)
    master.add(scene2, layer='bottom')
    assert scene1.start_time == 0.0
    assert scene2.start_time == pytest.approx(5.0)


def test_master_add_respects_explicit_start() -> None:
    master = MasterScene()
    scene1 = Scene()
    scene1.duration = 2.0
    scene2 = Scene()
    scene2.set_start_at(10.0)
    scene2.duration = 1.0
    scene3 = Scene()
    scene3.duration = 4.0
    master.add(scene1)
    master.add(scene2)
    master.add(scene3)
    assert scene1.start_time == 0.0
    assert scene2.start_time == pytest.approx(10.0)
    assert scene3.start_time == pytest.approx(11.0)
