from framekit.frame_base import FrameBase


class VideoElement(FrameBase):

    def __init__(self, video_path: str, scale: float = 1.0) -> None:
        raise NotImplementedError("VideoElement is not implemented yet")
    
    def render(self, time: float) -> None:
        raise NotImplementedError("VideoElement is not implemented yet")
