from services.analysis._shared import _check_leg_straightness
from services.analysis.leg_raise import _check_no_swing
from services.analysis.toes_to_bar import _check_tob_height, _detect_tob_rep_phases


def analyse_one_arm_toes_to_bar(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run form checks for a one-arm toes to bar.

    From a side camera, the form of a one-arm toes to bar is geometrically identical
    to the two-arm version — the hip angle signal, height check, and leg straightness
    check are all the same. The one-arm constraint is not detectable via pose landmarks
    (a single gripping hand is not distinguishable from the side). It is verified by
    the user filming with the gripping hand clearly visible.

    All analysis logic is imported directly from toes_to_bar.py — only the exercise
    name in the return dict changes.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "one_arm_toes_to_bar",
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

    phase_data = _detect_tob_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]

    top_frames = [reps[0][1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_tob_height(landmarks_per_frame, top_frames),
        _check_leg_straightness(landmarks_per_frame, top_frames),
        _check_no_swing(landmarks_per_frame),
    ]

    return {
        "exercise": "one_arm_toes_to_bar",
        "rep_count": genuine_reps,
        "checks": checks,
    }
