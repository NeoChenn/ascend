from pydantic import BaseModel


class Landmark(BaseModel):
    """
    A single body joint detected by MediaPipe.
    x and y are normalised screen coordinates (0.0–1.0).
    visibility is MediaPipe's confidence that the joint is visible (0.0–1.0).
    """
    x: float
    y: float
    z: float
    visibility: float


class PoseResult(BaseModel):
    """
    The pose data extracted from an entire video.
    landmarks_per_frame is a list with one entry per frame,
    each entry mapping joint names to their Landmark values.
    """
    frame_count: int
    landmarks_per_frame: list[dict[str, Landmark]]
