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


class FormCheck(BaseModel):
    """
    The result of a single form check (e.g. 'bottom extension').
    passed: True if the athlete's form met the threshold for this check.
    message: A human-readable explanation of the result.
    measurement: The actual measured value (e.g. angle in degrees), or None
                 for checks where a number isn't meaningful to surface.
    """
    name: str
    passed: bool
    message: str
    measurement: float | None = None


class FormFeedback(BaseModel):
    """
    All form feedback produced for a single video upload.
    exercise: Which exercise was analysed (e.g. 'pull_up').
    rep_count: How many complete reps were detected in the video.
    checks: List of individual form checks, each with a pass/fail result.
    """
    exercise: str
    rep_count: int
    checks: list[FormCheck]
