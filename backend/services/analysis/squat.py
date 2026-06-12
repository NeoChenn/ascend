from services.analysis._shared import (
    _check_torso_upright,
    _compute_knee_angles,
    _smooth_signal,
)


def _detect_squat_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each squat rep in the video.

    For a squat:
    - Top (standing, knees extended) → knee angle near 170–180° → local MAX
    - Bottom (squatting, knees bent)  → knee angle near 70–100°  → local MIN

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "knee_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_knee_angles(landmarks_per_frame), window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]

        # Bottom: deepest squat position, knees maximally bent (< 100° = at or below parallel)
        if is_local_min and smoothed[i] < 100:
            bottom_indices.append(i)
        # Top: standing position, knees nearly straight (> 150°)
        if is_local_max and smoothed[i] > 150:
            top_indices.append(i)

    # De-duplicate: enforce bottoms and tops must strictly alternate.
    all_events: list[tuple[int, str]] = sorted(
        [(idx, "bottom") for idx in bottom_indices] +
        [(idx, "top") for idx in top_indices]
    )
    deduped: list[list] = []
    for idx, kind in all_events:
        if deduped and deduped[-1][1] == kind:
            deduped[-1][0] = idx  # keep the more committed (later) event
        else:
            deduped.append([idx, kind])

    reps: list[tuple[int, int]] = [
        (deduped[i][0], deduped[i + 1][0])
        for i in range(len(deduped) - 1)
        if deduped[i][1] == "bottom" and deduped[i + 1][1] == "top"
    ]

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "knee_angles": smoothed}


def _check_squat_depth(
    knee_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete reaches parallel or below at the bottom of each rep.

    Parallel (thighs horizontal) corresponds to roughly 90° at the knee.
    We allow up to 100° to account for small measurement errors from the camera angle.
    """
    if not bottom_frame_indices:
        return {
            "name": "squat_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(knee_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle < 100

    if passed:
        message = f"Good depth — knee angle reached {avg_angle:.0f}° (at or below parallel)."
    else:
        message = (
            f"Knee angle at the bottom was {avg_angle:.0f}° — aim to reach parallel "
            "(thighs horizontal, ~90°). Squat deeper to work the full range of motion."
        )

    return {
        "name": "squat_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_squat_lockout(
    knee_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete fully extends their knees at the top of each rep.

    Full lockout (standing tall) should produce a knee angle above ~155°.
    Stopping short at the top reduces time under tension and is poor form.
    """
    if not top_frame_indices:
        return {
            "name": "squat_lockout",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(knee_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle > 155

    if passed:
        message = f"Good lockout at the top — knee angle was {avg_angle:.0f}°."
    else:
        message = (
            f"Knee angle at the top was only {avg_angle:.0f}° — "
            "stand up fully and lock out your knees at the top of each rep."
        )

    return {
        "name": "squat_lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_squat(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all squat form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "squat",
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

    phase_data = _detect_squat_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    knee_angles: list[float] = phase_data["knee_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_squat_depth(knee_angles, bottom_frames),
        _check_squat_lockout(knee_angles, top_frames),
        _check_torso_upright(landmarks_per_frame, bottom_frames),
    ]

    return {
        "exercise": "squat",
        "rep_count": genuine_reps,
        "checks": checks,
    }
