from services.analysis._shared import (
    _check_body_alignment,
    _compute_elbow_angles,
    _smooth_signal,
)


def _detect_pushup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each push-up rep in the video.

    For a push-up, the elbow angle signal is the OPPOSITE of a pull-up:
    - Bottom (chest near floor, arms bent) → elbow angle is small (~70–90°) → local MIN
    - Top (arms extended, plank position) → elbow angle is near 180° → local MAX

    Returns the same shape as _detect_pullup_rep_phases.
    """
    # Window=11 covers ~0.37 s at 30 fps, removing most landmark jitter while
    # keeping genuine rep transitions (which take at least 0.5 s) intact.
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame), window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: a local minimum below 100° (chest close to the floor)
        if is_local_min and smoothed[i] < 100:
            bottom_indices.append(i)
        # Top: a local maximum above 150° (arms close to fully extended)
        if is_local_max and smoothed[i] > 150:
            top_indices.append(i)

    # De-duplicate: enforce that bottoms and tops must strictly alternate.
    # Two consecutive bottoms (e.g. noise dip during descent) get merged into
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


def _check_pushup_top_extension(
    elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether arms are fully extended at the top of each push-up rep.

    The top position is a full plank with locked-out elbows. We use 160° as the
    threshold — below that, the athlete is not pressing all the way up.
    """
    if not top_frame_indices:
        return {
            "name": "top_extension",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle > 160

    if passed:
        message = f"Good lockout at the top — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the top was only {avg_angle:.0f}° — "
            "try to fully extend your arms at the top of each rep."
        )

    return {
        "name": "top_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_pushup_bottom_depth(
    elbow_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete lowers far enough on each rep (chest near floor).

    At full depth, the elbow angle is typically 70–90°. We use 100° as the
    threshold — above that, the chest is clearly not approaching the ground.
    """
    if not bottom_frame_indices:
        return {
            "name": "bottom_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle < 100

    if passed:
        message = f"Good depth at the bottom — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the bottom was {avg_angle:.0f}° — "
            "lower your chest closer to the ground for full range of motion."
        )

    return {
        "name": "bottom_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_push_up(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all push-up form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "push_up",
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
        "exercise": "push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
