from services.analysis._shared import (
    _check_leg_straightness,
    _compute_hip_angles,
    _smooth_signal,
)


def _detect_leg_raise_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each hanging leg raise rep.

    For a leg raise:
    - Bottom (legs hanging straight down) → shoulder-hip-ankle angle near 180° → local MAX
    - Top (legs raised to horizontal or above) → angle near 90° or below → local MIN

    This mirrors pull-up rep detection: local MAX = rest position, local MIN = peak effort.

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "hip_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_hip_angles(landmarks_per_frame), window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: legs hanging straight, hip angle near 180°
        if is_local_max and smoothed[i] > 160:
            bottom_indices.append(i)
        # Top: legs raised to at least horizontal (~90°)
        if is_local_min and smoothed[i] < 110:
            top_indices.append(i)

    all_events: list[tuple[int, str]] = sorted(
        [(idx, "bottom") for idx in bottom_indices] +
        [(idx, "top") for idx in top_indices]
    )
    deduped: list[list] = []
    for idx, kind in all_events:
        if deduped and deduped[-1][1] == kind:
            deduped[-1][0] = idx
        else:
            deduped.append([idx, kind])

    reps: list[tuple[int, int]] = [
        (deduped[i][0], deduped[i + 1][0])
        for i in range(len(deduped) - 1)
        if deduped[i][1] == "bottom" and deduped[i + 1][1] == "top"
    ]

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "hip_angles": smoothed}


def _check_leg_raise_height(
    hip_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether the legs reach at least horizontal at the top of each rep.

    A shoulder-hip-ankle angle below 110° means the legs are at or above horizontal
    (90° = exactly horizontal). We allow up to 110° to account for small measurement
    errors caused by the camera angle.
    """
    if not top_frame_indices:
        return {
            "name": "leg_raise_height",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(hip_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle < 110

    if passed:
        message = f"Good height — legs reached {avg_angle:.0f}° at the top (at or above horizontal)."
    else:
        message = (
            f"Hip angle at the top was {avg_angle:.0f}° — raise your legs higher. "
            "Aim to get your legs at least parallel to the floor (90°)."
        )

    return {
        "name": "leg_raise_height",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_no_swing(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Detect momentum-driven swinging on the bar.

    Swinging shows up as a sudden large vertical jump in hip position between
    consecutive frames. In MediaPipe coordinates, y decreases upward, so a sudden
    upward hip jerk appears as a sudden decrease in hip y. We flag any frame-to-frame
    hip y delta above 0.03 (roughly 22px in 720p) as a swing.

    We monitor the hips rather than the shoulders because the hips are the body part
    that generates and transmits the kipping momentum in a leg raise.
    """
    hip_y_values: list[float] = []

    for frame in landmarks_per_frame:
        avg_hip_y = (frame["left_hip"]["y"] + frame["right_hip"]["y"]) / 2
        hip_y_values.append(avg_hip_y)

    if len(hip_y_values) < 2:
        return {
            "name": "no_swing",
            "passed": True,
            "message": "Not enough frames to assess swinging.",
            "measurement": None,
        }

    max_delta = max(
        abs(hip_y_values[i] - hip_y_values[i - 1])
        for i in range(1, len(hip_y_values))
    )
    passed = max_delta < 0.03

    if passed:
        message = "No excessive swinging detected — movement looks controlled."
    else:
        message = (
            "Possible swinging detected — sudden hip movement suggests momentum is "
            "being used. Keep the movement controlled with no kipping."
        )

    return {
        "name": "no_swing",
        "passed": passed,
        "message": message,
        "measurement": round(max_delta, 4),
    }


def analyse_leg_raise(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all leg raise form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "leg_raise",
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

    phase_data = _detect_leg_raise_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    hip_angles: list[float] = phase_data["hip_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]  # noqa: F841
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_leg_raise_height(hip_angles, top_frames),
        _check_leg_straightness(landmarks_per_frame, top_frames),
        _check_no_swing(landmarks_per_frame),
    ]

    return {
        "exercise": "leg_raise",
        "rep_count": genuine_reps,
        "checks": checks,
    }
