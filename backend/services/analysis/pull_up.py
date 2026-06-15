from services.analysis._shared import (
    _check_body_alignment,
    _compute_elbow_angles,
    _smooth_signal,
)


def _detect_pullup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    window: int = 11,
) -> dict:
    """
    Identify the bottom and top of each pull-up rep in the video.

    For a pull-up:
    - Bottom (arms straight, hanging) → elbow angle is near 180° → local MAX
    - Top (arms bent, chin over bar) → elbow angle is small (~60°) → local MIN

    window: smoothing window size. Default 11 (~0.37 s at 30 fps) suits
    controlled reps. Pass a smaller value (e.g. 5) for explosive one-rep
    videos where the full movement is over in under a second.

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "elbow_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame), window=window)

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

    # De-duplicate: enforce that bottoms and tops must strictly alternate.
    # Two consecutive bottoms (e.g. noise at the hang position) get merged into
    # one by keeping the later index; same for consecutive tops.
    all_events: list[tuple[int, str]] = sorted(
        [(idx, "bottom") for idx in bottom_indices] +
        [(idx, "top") for idx in top_indices]
    )
    deduped: list[list] = []
    for idx, kind in all_events:
        if deduped and deduped[-1][1] == kind:
            deduped[-1][0] = idx   # replace with the more committed (later) event
        else:
            deduped.append([idx, kind])

    reps: list[tuple[int, int]] = [
        (deduped[i][0], deduped[i + 1][0])
        for i in range(len(deduped) - 1)
        if deduped[i][1] == "bottom" and deduped[i + 1][1] == "top"
    ]

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "elbow_angles": smoothed}


def _check_bottom_extension(
    elbow_angles: list[float],
    bottom_frame_indices: list[int],
    threshold: int = 160,
) -> dict:
    """
    Check whether arms are fully extended at the bottom of each rep.

    A fully straight arm has an elbow angle close to 180°. Default threshold
    is 160°. Pass a lower value (e.g. 155) for one-arm pull-ups where the
    single gripping arm reads slightly compressed from a side-on camera.
    """
    if not bottom_frame_indices:
        return {
            "name": "bottom_extension",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle > threshold

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

    We track hip y rather than shoulder y. In a strict pull-up the hips rise
    slowly and gradually; in a kip, the hips oscillate rapidly (backward arch →
    forward snap) producing sustained large frame-to-frame deltas.

    We use the 95th-percentile delta rather than the maximum. A single outlier
    frame (e.g. jumping to grab the bar at the start, or dropping off at the
    end) would fail a max-based check even on a perfectly strict rep. Genuine
    kipping produces many high-delta frames throughout the rep, so it still
    fails on the 95th percentile.
    """
    hip_y_values: list[float] = []

    for frame in landmarks_per_frame:
        avg_hip_y = (frame["left_hip"]["y"] + frame["right_hip"]["y"]) / 2
        hip_y_values.append(avg_hip_y)

    if len(hip_y_values) < 2:
        return {
            "name": "kipping",
            "passed": True,
            "message": "Not enough frames to assess kipping.",
            "measurement": None,
        }

    smoothed = _smooth_signal(hip_y_values, window=3)
    deltas = sorted(
        abs(smoothed[i] - smoothed[i - 1])
        for i in range(1, len(smoothed))
    )
    p95 = deltas[int(len(deltas) * 0.95)]
    passed = p95 < 0.05

    if passed:
        message = "No kipping detected — movement looks controlled."
    else:
        message = (
            "Possible kipping detected — sustained hip swinging suggests "
            "you may be using momentum to generate the pull."
        )

    return {
        "name": "kipping",
        "passed": passed,
        "message": message,
        "measurement": round(p95, 4),
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

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

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
