from services.analysis._shared import _check_body_alignment
from services.analysis.pull_up import (
    _check_bottom_extension,
    _check_top_flexion,
    _detect_pullup_rep_phases,
)


def _check_upper_arm_horizontal(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    flexed_frame_indices: list[int],
) -> dict:
    """
    Check that the upper arms reach horizontal at the bottom of the press.

    "90° handstand push-up" means the upper arms are parallel to the floor at the
    deepest point — not that the elbow angle is 90°. When the upper arm is
    horizontal, the shoulder and elbow sit at the same height:
    abs(shoulder_y - elbow_y) ≈ 0.

    We use a threshold of 0.05 (5% of normalised frame height, ~36px in 720p).
    This holds in the vertically-flipped coordinate space: flipping maps y → (1-y),
    so |y_shoulder - y_elbow| = |(1-y_s) - (1-y_e)| = |y_s - y_e|, unchanged.

    Args:
        landmarks_per_frame: Full per-frame landmark list.
        flexed_frame_indices: Indices of the most-bent frame(s) from rep detection.
    """
    if not flexed_frame_indices:
        return {
            "name": "upper_arm_horizontal",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    vertical_gaps: list[float] = []

    for idx in flexed_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]

        for shoulder_key, elbow_key in [
            ("left_shoulder", "left_elbow"),
            ("right_shoulder", "right_elbow"),
        ]:
            if (
                frame[shoulder_key]["visibility"] >= 0.5
                and frame[elbow_key]["visibility"] >= 0.5
            ):
                vertical_gaps.append(
                    abs(frame[shoulder_key]["y"] - frame[elbow_key]["y"])
                )

    if not vertical_gaps:
        return {
            "name": "upper_arm_horizontal",
            "passed": False,
            "message": (
                "Could not assess upper arm angle — "
                "shoulder or elbow landmarks were not visible at the bottom."
            ),
            "measurement": None,
        }

    avg_gap = sum(vertical_gaps) / len(vertical_gaps)
    passed = avg_gap < 0.05

    if passed:
        message = (
            f"Good depth — upper arms reached horizontal (vertical gap {avg_gap:.3f})."
        )
    else:
        message = (
            f"Upper arm vertical gap was {avg_gap:.3f} at the bottom "
            f"(target < 0.050). Lower your head further until your upper arms "
            "are parallel to the floor."
        )

    return {
        "name": "upper_arm_horizontal",
        "passed": passed,
        "message": message,
        "measurement": round(avg_gap, 4),
    }


def analyse_handstand_push_up_90(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all 90° handstand push-up form checks on the extracted per-frame landmark data.

    A 90° handstand push-up is a handstand push-up where the upper arms reach
    horizontal (parallel to the floor) at the deepest point of the press — the
    hardest standard range of motion for the movement.

    Detection is identical to handstand_push_up.py: the video is flipped vertically
    before MediaPipe (flip_vertical=True in pose_service.py) so the inverted person
    appears upright, and then pull-up style rep detection is applied. One additional
    check is added — _check_upper_arm_horizontal — which verifies shoulder and elbow
    sit at the same height at the most-bent frame.

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
            "exercise": "handstand_push_up_90",
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
    extended_frames = [first_rep[0]]
    flexed_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_bottom_extension(elbow_angles, extended_frames),
        _check_top_flexion(elbow_angles, flexed_frames),
        _check_upper_arm_horizontal(landmarks_per_frame, flexed_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "handstand_push_up_90",
        "rep_count": genuine_reps,
        "checks": checks,
    }
