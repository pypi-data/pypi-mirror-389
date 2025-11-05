
from __future__ import annotations

from pathlib import Path
from typing import Optional

import av
import numpy as np


class AudioElement:
    SAMPLE_RATE = 48_000
    CHANNELS = 2

    def __init__(self, audio_path: str) -> None:
        self.audio_path = Path(audio_path)
        self.loop = False
        self.volume = 1.0
        self.muted = False
        self.duration = 0.0
        self.start_time = 0.0
        self._decoded_rate: int = 0
        self._decoded_duration: float = 0.0
        self._buffer: Optional[np.ndarray] = None
        self._decode()

    def _decode(self) -> None:
        if not self.audio_path.exists():
            self._buffer = np.zeros((0, self.CHANNELS), dtype=np.float32)
            self._decoded_rate = self.SAMPLE_RATE
            self._decoded_duration = 0.0
            return
        container = av.open(str(self.audio_path))
        try:
            stream = next((s for s in container.streams if s.type == 'audio'), None)
            if stream is None:
                self._buffer = np.zeros((0, self.CHANNELS), dtype=np.float32)
                self._decoded_rate = self.SAMPLE_RATE
                self._decoded_duration = 0.0
                return
            frames = []
            detected_rate = stream.rate or stream.codec_context.sample_rate or 0
            for frame in container.decode(stream):
                if not detected_rate:
                    detected_rate = frame.sample_rate or 0
                array = frame.to_ndarray()
                if array.ndim == 1:
                    array = array.reshape(1, -1)
                if array.shape[0] == 0:
                    continue
                if array.shape[0] == 1:
                    array = np.vstack((array, array))
                elif array.shape[0] > 2:
                    array = array[:2]
                original_dtype = array.dtype
                numeric = array.astype(np.float32)
                if np.issubdtype(original_dtype, np.integer):
                    info = np.iinfo(original_dtype)
                    scale = float(max(abs(info.min), info.max))
                    if scale > 0.0:
                        numeric /= scale
                frames.append(numeric.T)
            if not frames:
                self._buffer = np.zeros((0, self.CHANNELS), dtype=np.float32)
                self._decoded_rate = detected_rate or self.SAMPLE_RATE
                self._decoded_duration = 0.0
                return
            concatenated = np.concatenate(frames, axis=0)
            self._decoded_rate = detected_rate or self.SAMPLE_RATE
            self._buffer = concatenated.astype(np.float32)
            self._decoded_duration = concatenated.shape[0] / float(self._decoded_rate)
        finally:
            container.close()

    def set_start_at(self, time: float) -> 'AudioElement':
        self.start_time = max(time, 0.0)
        return self

    def set_volume(self, volume: float) -> 'AudioElement':
        self.volume = max(volume, 0.0)
        return self

    def mute(self) -> 'AudioElement':
        self.muted = True
        return self

    def unmute(self) -> 'AudioElement':
        self.muted = False
        return self

    def set_duration(self, duration: float) -> 'AudioElement':
        self.duration = max(duration, 0.0)
        return self

    def set_loop(self, loop: bool = True) -> 'AudioElement':
        self.loop = loop
        return self

    def _resample(self, buffer: np.ndarray) -> np.ndarray:
        if buffer.size == 0 or self._decoded_rate == self.SAMPLE_RATE:
            return buffer
        ratio = self.SAMPLE_RATE / float(self._decoded_rate)
        target = int(round(buffer.shape[0] * ratio))
        if target <= 1:
            return np.zeros((0, buffer.shape[1]), dtype=np.float32)
        x_old = np.linspace(0.0, 1.0, buffer.shape[0], endpoint=False)
        x_new = np.linspace(0.0, 1.0, target, endpoint=False)
        channels = [np.interp(x_new, x_old, buffer[:, idx]) for idx in range(buffer.shape[1])]
        stacked = np.stack(channels, axis=1).astype(np.float32)
        return stacked

    def _effective_duration(self) -> float:
        if self.duration > 0.0:
            return self.duration
        return self._decoded_duration

    def render(self) -> np.ndarray:
        if self._buffer is None:
            return np.zeros((0, self.CHANNELS), dtype=np.float32)
        base = self._resample(self._buffer)
        effective_duration = self._effective_duration()
        if effective_duration <= 0.0:
            return np.zeros((0, self.CHANNELS), dtype=np.float32)
        target_samples = int(round(effective_duration * self.SAMPLE_RATE))
        if target_samples <= 0:
            return np.zeros((0, self.CHANNELS), dtype=np.float32)
        if base.shape[0] >= target_samples:
            clipped = base[:target_samples]
        else:
            if not self.loop or base.shape[0] == 0:
                padding = np.zeros((target_samples - base.shape[0], base.shape[1]), dtype=np.float32)
                clipped = np.vstack((base, padding))
            else:
                repeats = target_samples // base.shape[0]
                remainder = target_samples % base.shape[0]
                tiled = np.vstack([base] * repeats) if repeats else np.zeros((0, base.shape[1]), dtype=np.float32)
                if remainder:
                    tiled = np.vstack((tiled, base[:remainder]))
                clipped = tiled[:target_samples]
        if self.muted or self.volume == 0.0:
            return np.zeros_like(clipped)
        return clipped * self.volume

    def total_duration(self) -> float:
        return self._effective_duration()
