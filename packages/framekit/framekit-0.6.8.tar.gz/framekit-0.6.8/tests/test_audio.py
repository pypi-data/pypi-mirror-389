from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from framekit.audio_element import AudioElement
from framekit.master_scene_element import MasterScene
from framekit.scene_element import Scene


def _write_wave(path: Path, duration: float = 0.1, rate: int = 22_050) -> None:
    total_samples = int(duration * rate)
    if total_samples == 0:
        total_samples = rate
    t = np.linspace(0.0, duration, total_samples, endpoint=False)
    tone = (0.25 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    stereo = np.stack((tone, tone), axis=1)
    pcm = (stereo * 32767.0).astype(np.int16)
    with wave.open(str(path), 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def test_audio_element_render_and_mute(tmp_path: Path) -> None:
    wav_path = tmp_path / 'tone.wav'
    _write_wave(wav_path)
    element = AudioElement(str(wav_path)).set_duration(0.1).set_volume(0.5)
    samples = element.render()
    assert samples.shape[1] == AudioElement.CHANNELS
    assert samples.dtype == np.float32
    assert np.all(np.abs(samples) <= 1.0)
    muted = element.mute().render()
    assert np.allclose(muted, 0.0)
    unmuted = element.unmute().render()
    assert np.any(np.abs(unmuted) > 0.0)


def test_scene_add_audio_track(tmp_path: Path) -> None:
    wav_path = tmp_path / 'tone.wav'
    _write_wave(wav_path)
    scene = Scene()
    audio = AudioElement(str(wav_path))
    scene.add(audio)
    assert audio in scene.audio


def test_master_scene_renders_with_audio(tmp_path: Path) -> None:
    wav_path = tmp_path / 'tone.wav'
    _write_wave(wav_path, duration=0.2)
    scene = Scene()
    audio = AudioElement(str(wav_path)).set_duration(0.2)
    scene.add(audio)
    output = tmp_path / 'out.mp4'
    master = MasterScene(output_filename=str(output), width=64, height=64, fps=10, quality='low')
    master.add(scene)
    master.render()
    assert output.exists()
    assert output.stat().st_size > 0
