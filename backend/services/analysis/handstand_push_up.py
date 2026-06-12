from services.analysis._shared import _check_body_alignment
from services.analysis.pull_up import (
    _check_bottom_extension,
    _check_top_flexion,
    _detect_pullup_rep_phases,
)


def analyse_handstand_push_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all handstand push-up form checks on the extracted per-frame landmark data.

    The video is submitted normally (floor at the bottom). The backend flips it
    vertically before MediaPipe runs (flip_vertical=True in pose_service.py), so the
    model sees an upright person with arms raised overhead. In the flipped view, a
    handstand push-up looks exactly like a pull-up: the person starts with arms
    extended (elbows ~170°), bends them until the head approaches the floor
    (elbows ~90°), then extends back.

    We therefore reuse _detect_pullup_rep_phases directly:
      - local MAX > 150° → "bottom" frame = arms extended = lockout position
      - local MIN < 110° → "top" frame   = arms flexed  = head near floor

    Only the first detected rep is evaluated (first-rep-only policy shared by all
    dynamic analysers — prevents penalising a clean rep for a weaker follow-up).

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video (with flip_vertical=True
            applied upstream in pose_service.py) — a list of dicts, one per frame, each
            mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "handstand_push_up",
            "rep_count": 0,
            "checks": [
                {
                    "name": "insufficient_data",
                    "passed": False,
                    "message": (
                        "Not enough pose data was detected. "
                        "Make sure you are clearly visible in the video."
                    ),
                    "measurement": None,
                }
            ],
        }

    phase_data = _detect_pullup_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    first_rep = reps[0]
    # "bottom" in pull-up terms = arms extended = lockout frame for HSPu
    # "top" in pull-up terms    = arms flexed  = head near floor for HSPu
    extended_frames = [first_rep[0]]
    flexed_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        # Checks elbow > 160° at the extended frame — arm lockout at press top
        _check_bottom_extension(elbow_angles, extended_frames),
        # Checks elbow < 90° at the flexed frame — full depth, head near floor
        _check_top_flexion(elbow_angles, flexed_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "handstand_push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
