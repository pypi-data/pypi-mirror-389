import sys
from pathlib import Path

import av

sys.path.append(str(Path(__file__).resolve().parents[1]))

from framekit import MasterScene, Scene, TextElement


def test_master_scene_renders_hello_world(tmp_path) -> None:
    output = tmp_path / 'hello_world.mp4'
    master = MasterScene(output_filename=str(output), width=640, height=360, fps=30)
    scene = Scene().set_duration(3.0)
    text = TextElement('hello world').set_size(64).set_color((255, 255, 255)).set_position(320, 180, anchor='center').set_duration(3.0)
    scene.add(text)
    master.add(scene)
    master.render()
    assert output.exists()
    container = av.open(str(output))
    try:
        stream = container.streams.video[0]
        frames = list(container.decode(stream))
    finally:
        container.close()
    assert len(frames) == 90
    first_frame = frames[0].to_ndarray(format='rgb24')
    assert first_frame.max() > 200
