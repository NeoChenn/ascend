from services.analysis._shared import _check_body_alignment
from services.analysis.push_up import (
    _check_pushup_bottom_depth,
    _check_pushup_top_extension,
    _detect_pushup_rep_phases,
)


def analyse_one_arm_push_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run form checks for a one-arm push-up.

    From a side camera, the form of a one-arm push-up is geometrically identical to
    the two-arm version — the elbow angle signal, depth check, and body alignment are
    all the same. The one-arm constraint is not detectable from pose landmarks alone
    (a single supporting hand looks identical from the side). It is verified by the
    user filming with the gripping arm clearly visible in frame.

    All analysis logic is imported directly from push_up.py — only the exercise
    name in the return dict changes. This mirrors the one_arm_pull_up pattern.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "one_arm_push_up",
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

    phase_data = _detect_pushup_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_pushup_top_extension(elbow_angles, top_frames),
        _check_pushup_bottom_depth(elbow_angles, bottom_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "one_arm_push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
