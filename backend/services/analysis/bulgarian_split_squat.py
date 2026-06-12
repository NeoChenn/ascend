from services.analysis._shared import (
    _check_torso_upright,
    _smooth_signal,
    calculate_angle,
)


def _identify_working_leg(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_indices: list[int],
) -> str:
    """
    Determine which leg is the front (working) leg.

    The front leg bends much more deeply than the rear leg at the bottom of the
    movement, so it has the smaller hip-knee-ankle angle. We sum the knee angles
    for each side across all detected bottom frames and pick the smaller sum.
    """
    if not bottom_indices:
        return "left"  # arbitrary fallback when no reps detected

    left_sum = 0.0
    right_sum = 0.0

    for idx in bottom_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]
        left_sum += calculate_angle(frame["left_hip"], frame["left_knee"], frame["left_ankle"])
        right_sum += calculate_angle(frame["right_hip"], frame["right_knee"], frame["right_ankle"])

    return "left" if left_sum < right_sum else "right"


def _detect_bss_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify bottom and top positions of each Bulgarian split squat rep.

    Strategy: use min(left_knee, right_knee) per frame as the tracking signal.
    The front leg is always more bent, so the minimum reliably tracks it without
    needing to know which leg is working before we start.

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "left_angles":    [float, ...],   # raw, one per frame
          "right_angles":   [float, ...],   # raw, one per frame
          "working_angles": [float, ...]    # smoothed min(left, right) per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    left_angles = [
        calculate_angle(f["left_hip"], f["left_knee"], f["left_ankle"])
        for f in landmarks_per_frame
    ]
    right_angles = [
        calculate_angle(f["right_hip"], f["right_knee"], f["right_ankle"])
        for f in landmarks_per_frame
    ]

    working_raw = [min(l, r) for l, r in zip(left_angles, right_angles)]
    smoothed = _smooth_signal(working_raw, window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]

        # BSS allows slightly less depth than a back squat (105° threshold vs 100°)
        if is_local_min and smoothed[i] < 105:
            bottom_indices.append(i)
        if is_local_max and smoothed[i] > 150:
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

    return {
        "reps": reps,
        "left_angles": left_angles,
        "right_angles": right_angles,
        "working_angles": smoothed,
    }


def _check_bss_depth(
    working_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether the front knee reaches at least 90–105° at the bottom of the lunge.

    The elevated rear foot limits range of motion slightly compared to a full back
    squat, so we use 105° as the pass threshold (vs 100° for squats).
    """
    if not bottom_frame_indices:
        return {
            "name": "bss_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(working_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle < 105

    if passed:
        message = f"Good depth — front knee reached {avg_angle:.0f}° at the bottom."
    else:
        message = (
            f"Front knee angle at the bottom was {avg_angle:.0f}° — "
            "lower your hips until your front thigh is close to horizontal."
        )

    return {
        "name": "bss_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_bss_rear_knee(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_frame_indices: list[int],
    working_leg: str,
) -> dict:
    """
    Check that the rear knee descends below the level of the elevated rear foot.

    In MediaPipe normalised coords, y increases downward. When the rear foot is
    elevated on a bench, the rear ankle has a smaller y-value than the floor.
    A properly executed lunge drives the rear knee below the rear ankle level
    (rear_knee_y > rear_ankle_y), confirming full depth was reached.

    We require the gap to be at least 0.02 (≈ 2% of frame height) so that
    borderline cases don't falsely pass.
    """
    rear_leg = "right" if working_leg == "left" else "left"
    knee_key = f"{rear_leg}_knee"
    ankle_key = f"{rear_leg}_ankle"

    gaps: list[float] = []

    for idx in bottom_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]
        knee = frame[knee_key]
        ankle = frame[ankle_key]

        if knee["visibility"] < 0.5 or ankle["visibility"] < 0.5:
            continue

        # Positive gap means knee is below the elevated ankle = properly descended
        gaps.append(knee["y"] - ankle["y"])

    if not gaps:
        return {
            "name": "rear_knee_descent",
            "passed": True,
            "message": (
                "Rear knee not clearly visible — ensure your full body is in frame. "
                "Check passed by default."
            ),
            "measurement": None,
        }

    avg_gap = sum(gaps) / len(gaps)
    passed = avg_gap > 0.02

    if passed:
        message = "Good — rear knee descended below the level of the elevated rear foot."
    else:
        message = (
            "Rear knee did not descend below the rear foot level. "
            "Lower your hips more to get a full range of motion on each rep."
        )

    return {
        "name": "rear_knee_descent",
        "passed": passed,
        "message": message,
        "measurement": round(avg_gap, 3),
    }


def analyse_bulgarian_split_squat(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all Bulgarian split squat form checks on the per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "bulgarian_split_squat",
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

    phase_data = _detect_bss_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    working_angles: list[float] = phase_data["working_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]  # noqa: F841 — available for future checks

    working_leg = _identify_working_leg(landmarks_per_frame, bottom_frames)
    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_bss_depth(working_angles, bottom_frames),
        _check_bss_rear_knee(landmarks_per_frame, bottom_frames, working_leg),
        _check_torso_upright(landmarks_per_frame, bottom_frames),
    ]

    return {
        "exercise": "bulgarian_split_squat",
        "rep_count": genuine_reps,
        "checks": checks,
    }
