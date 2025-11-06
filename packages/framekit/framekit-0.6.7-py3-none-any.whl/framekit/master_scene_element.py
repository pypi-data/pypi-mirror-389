
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Dict, Literal, Optional, Set, Tuple

import av
import moderngl
import numpy as np
from PIL import Image
from tqdm import tqdm

from .audio_element import AudioElement
from .scene_element import Scene


class MasterScene:
    def __init__(self, output_filename: str = 'output_video.mp4', width: int = 1920, height: int = 1080, fps: int = 60, quality: Literal['low', 'medium', 'high'] = 'medium') -> None:
        self._explicit_duration: Optional[float] = None
        self.output_filename = output_filename
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        self.scenes: list[Scene] = []
        self._ctx: Optional[moderngl.Context] = None
        self._program: Optional[moderngl.Program] = None
        self._quad: Optional[moderngl.VertexArray] = None
        self._framebuffer: Optional[moderngl.Framebuffer] = None
        self._texture_cache: Dict[int, Tuple[moderngl.Texture, Tuple[int, int]]] = {}
        self._timeline: list[Scene] = []

    @property
    def duration(self) -> float:
        if self._explicit_duration is not None:
            return self._explicit_duration
        scopes = self._timeline if self._timeline else self.scenes
        if not scopes:
            return 0.0
        total = 0.0
        for scene in scopes:
            total = max(total, scene.start_time + scene.duration)
        return total

    @duration.setter
    def duration(self, value: float) -> None:
        self._explicit_duration = max(value, 0.0)

    def add(self, scene: Scene, layer: Literal['top', 'bottom'] = 'top') -> 'MasterScene':
        scene.set_canvas(self.width, self.height)
        if scene not in self._timeline:
            self._timeline.append(scene)
        pointer = 0.0
        for timeline_scene in self._timeline:
            if getattr(timeline_scene, '_start_time_locked', False):
                pointer = max(pointer, timeline_scene.start_time + timeline_scene.duration)
                continue
            timeline_scene.start_time = pointer
            pointer += timeline_scene.duration
        if layer == 'top':
            self.scenes.append(scene)
        else:
            self.scenes.insert(0, scene)
        return self

    def set_output(self, filename: str) -> 'MasterScene':
        self.output_filename = filename
        return self

    def render(self) -> None:
        if not self.scenes:
            return

        def scene_end(scene: Scene, offset: float) -> float:
            base = offset + scene.start_time
            durations = [base + scene.duration]
            durations.extend(base + element.start_time + element.duration for element in scene.elements)
            durations.extend(base + audio.start_time + audio.total_duration() for audio in scene.audio)
            durations.extend(scene_end(child, base) for child in scene.scenes)
            return max(durations)

        total_duration = max(scene_end(scene, 0.0) for scene in self.scenes)
        total_frames = int(np.ceil(total_duration * self.fps))
        if total_frames == 0:
            return
        audio_tracks: list[tuple[AudioElement, float]] = []

        def collect_audio(scene: Scene, offset: float) -> None:
            base = offset + scene.start_time
            for audio in scene.audio:
                audio_tracks.append((audio, base + audio.start_time))
            for child in scene.scenes:
                collect_audio(child, base)

        for scene in self.scenes:
            collect_audio(scene, 0.0)
        mix_buffer: Optional[np.ndarray] = None
        sample_rate = AudioElement.SAMPLE_RATE
        channels = AudioElement.CHANNELS
        total_audio_samples = int(np.ceil(total_duration * sample_rate))
        if audio_tracks and total_audio_samples > 0:
            # ---------------------------------------------------------
            # Mix audio buffers from every scene into a single timeline
            # ---------------------------------------------------------
            mix = np.zeros((total_audio_samples, channels), dtype=np.float32)
            for audio, offset in audio_tracks:
                rendered = audio.render()
                if rendered.size == 0:
                    continue
                start_index = max(int(round(offset * sample_rate)), 0)
                if start_index >= total_audio_samples:
                    continue
                end_index = min(total_audio_samples, start_index + rendered.shape[0])
                if end_index <= start_index:
                    continue
                mix[start_index:end_index] += rendered[:end_index - start_index]
            mix_buffer = np.clip(mix, -1.0, 1.0)

        bitrate_map = {'low': 1_000_000, 'medium': 3_000_000, 'high': 6_000_000}
        output_path = Path(self.output_filename)
        if output_path.parent != Path('.'):
            # ---------------------------------------------------------
            # Create the parent directory once before writing output
            # ---------------------------------------------------------
            output_path.parent.mkdir(parents=True, exist_ok=True)
        container = av.open(str(output_path), mode='w')
        try:
            try:
                stream = container.add_stream('libx264', rate=self.fps)
            except av.AVError:
                stream = container.add_stream('mpeg4', rate=self.fps)
            stream.width = self.width
            stream.height = self.height
            stream.pix_fmt = 'yuv420p'
            stream.bit_rate = bitrate_map[self.quality]
            audio_stream = None
            layout = None
            if mix_buffer is not None:
                layout_map = {1: 'mono', 2: 'stereo'}
                layout = layout_map.get(channels)
                if layout is None:
                    raise ValueError(f'Unsupported channel count: {channels}')
                audio_stream = container.add_stream('aac', rate=sample_rate, layout=layout)
                audio_stream.time_base = Fraction(1, sample_rate)
            frame_indices = tqdm(range(total_frames), desc='Rendering', unit='frame')
            use_gpu = False
            try:
                self._prepare_gpu()
                self._ensure_framebuffer()
                use_gpu = self._ctx is not None and self._framebuffer is not None
            except Exception:
                use_gpu = False
                if self._framebuffer is not None:
                    self._framebuffer.release()
                self._framebuffer = None
                self._ctx = None
                self._program = None
                self._quad = None
                for texture, _ in self._texture_cache.values():
                    texture.release()
                self._texture_cache.clear()
            for frame_index in frame_indices:
                time_point = frame_index / self.fps
                if use_gpu:
                    frame_array = self._render_frame_gpu(time_point)
                else:
                    base = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
                    for scene in self.scenes:
                        rendered = scene.render(time_point)
                        if rendered is None:
                            continue
                        base = Image.alpha_composite(base, rendered)
                    rgb_bytes = base.convert('RGB').tobytes()
                    frame_array = np.frombuffer(rgb_bytes, dtype=np.uint8).reshape((self.height, self.width, 3))
                video_frame = av.VideoFrame.from_ndarray(frame_array, format='rgb24')
                video_frame.pts = frame_index
                video_frame.time_base = Fraction(1, self.fps)
                for packet in stream.encode(video_frame):
                    container.mux(packet)
            for packet in stream.encode(None):
                container.mux(packet)
            if audio_stream and mix_buffer is not None and layout is not None:
                step = sample_rate
                pts = 0
                for index in range(0, mix_buffer.shape[0], step):
                    chunk = mix_buffer[index:index + step]
                    raw = np.ascontiguousarray(chunk.T * 32767.0, dtype=np.int16)
                    frame = av.AudioFrame.from_ndarray(raw, format='s16p', layout=layout)
                    frame.sample_rate = sample_rate
                    frame.pts = pts
                    frame.time_base = Fraction(1, sample_rate)
                    pts += chunk.shape[0]
                    for packet in audio_stream.encode(frame):
                        container.mux(packet)
                for packet in audio_stream.encode(None):
                    container.mux(packet)
        finally:
            container.close()

    def _prepare_gpu(self) -> None:
        if self._ctx is None:
            self._ctx = moderngl.create_standalone_context()
            self._ctx.enable(moderngl.BLEND)
            self._ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
            quad_data = np.array(
                [
                    -1.0,
                    -1.0,
                    0.0,
                    0.0,
                    1.0,
                    -1.0,
                    1.0,
                    0.0,
                    -1.0,
                    1.0,
                    0.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                ],
                dtype='f4',
            )
            vertex_shader = '''
                #version 330
                in vec2 in_pos;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    v_uv = in_uv;
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                }
            '''
            fragment_shader = '''
                #version 330
                in vec2 v_uv;
                out vec4 fragColor;
                uniform sampler2D tex0;
                void main() {
                    fragColor = texture(tex0, v_uv);
                }
            '''
            program = self._ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
            buffer = self._ctx.buffer(quad_data.tobytes())
            self._program = program
            self._quad = self._ctx.simple_vertex_array(program, buffer, 'in_pos', 'in_uv')
        if self._ctx is None:
            raise RuntimeError('Failed to initialize moderngl context')
        self._ctx.viewport = (0, 0, self.width, self.height)

    def _ensure_framebuffer(self) -> None:
        if self._ctx is None:
            return
        if self._framebuffer and self._framebuffer.size == (self.width, self.height):
            return
        if self._framebuffer is not None:
            self._framebuffer.release()
        color = self._ctx.texture((self.width, self.height), components=4)
        self._framebuffer = self._ctx.framebuffer(color_attachments=[color])

    def _acquire_texture(self, image: Image.Image) -> moderngl.Texture:
        if self._ctx is None:
            raise RuntimeError('GPU context not ready')
        key = id(image)
        cached = self._texture_cache.get(key)
        size = image.size
        if cached and cached[1] == size:
            return cached[0]
        data = image.convert('RGBA').tobytes()
        texture = self._ctx.texture(size, components=4, data=data)
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        if cached:
            cached[0].release()
        self._texture_cache[key] = (texture, size)
        return texture

    def _release_unused_textures(self, used: Set[int]) -> None:
        unused = [key for key in self._texture_cache if key not in used]
        for key in unused:
            texture, _ = self._texture_cache.pop(key)
            texture.release()

    def _render_frame_gpu(self, time_point: float) -> np.ndarray:
        if self._ctx is None or self._program is None or self._quad is None or self._framebuffer is None:
            raise RuntimeError('GPU resources are not ready')
        self._framebuffer.use()
        self._framebuffer.clear(0.0, 0.0, 0.0, 0.0)
        used: Set[int] = set()
        # ---------------------------------------------------------
        # Draw each scene as a textured quad with alpha blending
        # ---------------------------------------------------------
        for scene in self.scenes:
            rendered = scene.render(time_point)
            if rendered is None:
                continue
            texture = self._acquire_texture(rendered)
            used.add(id(rendered))
            texture.use(location=0)
            self._program['tex0'].value = 0
            self._quad.render(mode=moderngl.TRIANGLE_STRIP)
        self._release_unused_textures(used)
        frame_bytes = self._framebuffer.read(components=3, alignment=1)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((self.height, self.width, 3))
        return frame_array
