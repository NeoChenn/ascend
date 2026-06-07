from services.analysis._shared import (
    _check_body_alignment,
    _compute_elbow_angles,
    _smooth_signal,
)


def _detect_pullup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each pull-up rep in the video.

    For a pull-up:
    - Bottom (arms straight, hanging) → elbow angle is near 180° → local MAX
    - Top (arms bent, chin over bar) → elbow angle is small (~60°) → local MIN

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "elbow_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame))

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: a local maximum above 150° (arms close to straight)
        if is_local_max and smoothed[i] > 150:
            bottom_indices.append(i)
        # Top: a local minimum below 110° (arms well bent, chin likely over bar)
        if is_local_min and smoothed[i] < 110:
            top_indices.append(i)

    reps: list[tuple[int, int]] = []
    for bottom_idx in bottom_indices:
        next_top = next((t for t in top_indices if t > bottom_idx), None)
        if next_top is not None:
            reps.append((bottom_idx, next_top))

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "elbow_angles": smoothed}


def _check_bottom_extension(
    elbow_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether arms are fully extended at the bottom of each rep.

    A fully straight arm has an elbow angle close to 180°. We use 160° as the
    threshold — anything below that means the athlete is not fully straightening
    between reps, which reduces range of motion and pulling strength development.
    """
    if not bottom_frame_indices:
        return {
            "name": "bottom_extension",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle > 160

    if passed:
        message = f"Good full extension at the bottom — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the bottom was only {avg_angle:.0f}° — "
            "try to fully straighten your arms between reps."
        )

    return {
        "name": "bottom_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_top_flexion(
    elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete pulls high enough at the top of each rep.

    An elbow angle below 90° at the top typically means the chin has cleared
    the bar. Above 90° usually means the rep is incomplete.
    """
    if not top_frame_indices:
        return {
            "name": "top_flexion",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle < 90

    if passed:
        message = (
            f"Good height at the top — average elbow angle {avg_angle:.0f}°, "
            "chin is likely clearing the bar."
        )
    else:
        message = (
            f"Elbow angle at the top was {avg_angle:.0f}° — "
            "pull higher so your chin clears the bar."
        )

    return {
        "name": "top_flexion",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_kipping(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Check for kipping — using a hip swing to generate upward momentum.

    Kipping shows up as a sudden large upward jump in shoulder position between
    consecutive frames. In MediaPipe's coordinate system, y decreases as you
    move up, so a sudden decrease in shoulder y indicates a fast upward jerk.

    A frame-to-frame change > 0.03 (roughly 22px in 720p) suggests kipping.
    """
    shoulder_y_values: list[float] = []

    for frame in landmarks_per_frame:
        avg_shoulder_y = (frame["left_shoulder"]["y"] + frame["right_shoulder"]["y"]) / 2
        shoulder_y_values.append(avg_shoulder_y)

    if len(shoulder_y_values) < 2:
        return {
            "name": "kipping",
            "passed": True,
            "message": "Not enough frames to assess kipping.",
            "measurement": None,
        }

    max_delta = max(
        abs(shoulder_y_values[i] - shoulder_y_values[i - 1])
        for i in range(1, len(shoulder_y_values))
    )
    passed = max_delta < 0.03

    if passed:
        message = "No kipping detected — movement looks controlled."
    else:
        message = (
            "Possible kipping detected — sudden upward shoulder movement suggests "
            "you may be using hip swing to generate momentum."
        )

    return {
        "name": "kipping",
        "passed": passed,
        "message": message,
        "measurement": round(max_delta, 4),
    }


def analyse_pull_up(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all pull-up form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "pull_up",
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

    bottom_frames = [r[0] for r in reps]
    top_frames = [r[1] for r in reps]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_bottom_extension(elbow_angles, bottom_frames),
        _check_top_flexion(elbow_angles, top_frames),
        _check_body_alignment(landmarks_per_frame),
        _check_kipping(landmarks_per_frame),
    ]

    return {
        "exercise": "pull_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
