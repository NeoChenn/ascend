from services.analysis._shared import (
    _smooth_signal,
    calculate_angle,
)


def _identify_working_leg(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_indices: list[int],
) -> str:
    """
    Determine which leg is performing the pistol squat.

    The working leg bends deeply; the free leg extends forward and stays straight.
    The working leg therefore has the smaller hip-knee-ankle angle at the bottom.
    """
    if not bottom_indices:
        return "left"

    left_sum = 0.0
    right_sum = 0.0

    for idx in bottom_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]
        left_sum += calculate_angle(frame["left_hip"], frame["left_knee"], frame["left_ankle"])
        right_sum += calculate_angle(frame["right_hip"], frame["right_knee"], frame["right_ankle"])

    return "left" if left_sum < right_sum else "right"


def _detect_pistol_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify bottom and top positions of each pistol squat rep.

    A pistol squat requires full knee flexion — the bottom threshold is stricter
    (< 80°) than for a regular squat (< 100°). We use min(left, right) per frame
    to track the working leg without needing to know which it is in advance.

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "left_angles":    [float, ...],
          "right_angles":   [float, ...],
          "working_angles": [float, ...]   # smoothed
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

        # Pistol squat requires deep knee flexion — stricter than a regular squat
        if is_local_min and smoothed[i] < 80:
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


def _check_pistol_depth(
    working_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check that the working knee reaches full depth at the bottom (< 80°).

    A true pistol squat demands full knee flexion — the hips pass below the
    knees. At that depth the knee angle is typically 60–80°.
    """
    if not bottom_frame_indices:
        return {
            "name": "pistol_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(working_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle < 80

    if passed:
        message = f"Excellent depth — working knee reached {avg_angle:.0f}° at the bottom."
    else:
        message = (
            f"Working knee angle at the bottom was {avg_angle:.0f}°. "
            "A pistol squat requires full depth — lower your hips past your knee level."
        )

    return {
        "name": "pistol_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_pistol_lockout(
    working_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the working leg fully extends at the top of each rep.

    Standing tall on one leg with a locked knee should produce an angle above 155°.
    """
    if not top_frame_indices:
        return {
            "name": "pistol_lockout",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(working_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle > 155

    if passed:
        message = f"Good lockout at the top — working knee was {avg_angle:.0f}°."
    else:
        message = (
            f"Working knee at the top was only {avg_angle:.0f}° — "
            "fully straighten your standing leg between reps."
        )

    return {
        "name": "pistol_lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_pistol_free_leg(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_frame_indices: list[int],
    working_leg: str,
) -> dict:
    """
    Check that the free leg is extended forward at the bottom of the pistol.

    The free leg must be held straight and elevated in front of the body — if the
    hip-knee-ankle angle is above 150° the leg is adequately extended. A tucked or
    dropped free leg (smaller angle) is a common fault that makes the movement
    easier but disqualifies it as a true pistol squat.
    """
    free_leg = "right" if working_leg == "left" else "left"
    hip_key = f"{free_leg}_hip"
    knee_key = f"{free_leg}_knee"
    ankle_key = f"{free_leg}_ankle"

    angles: list[float] = []

    for idx in bottom_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]

        if any(frame[k]["visibility"] < 0.5 for k in [hip_key, knee_key, ankle_key]):
            continue

        angles.append(calculate_angle(frame[hip_key], frame[knee_key], frame[ankle_key]))

    if not angles:
        return {
            "name": "free_leg_extension",
            "passed": False,
            "message": (
                "Could not assess the free leg — ensure your full body "
                "is visible from head to toe in the video."
            ),
            "measurement": None,
        }

    avg_angle = sum(angles) / len(angles)
    passed = avg_angle > 150

    if passed:
        message = f"Good free leg extension — angle was {avg_angle:.0f}° (leg extended forward)."
    else:
        message = (
            f"Free leg angle was {avg_angle:.0f}°. "
            "Keep your free leg straight and extended in front — "
            "don't let it drop or bend at the knee."
        )

    return {
        "name": "free_leg_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_pistol_squat(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all pistol squat form checks on the per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "pistol_squat",
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

    phase_data = _detect_pistol_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    working_angles: list[float] = phase_data["working_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    working_leg = _identify_working_leg(landmarks_per_frame, bottom_frames)
    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_pistol_depth(working_angles, bottom_frames),
        _check_pistol_lockout(working_angles, top_frames),
        _check_pistol_free_leg(landmarks_per_frame, bottom_frames, working_leg),
    ]

    return {
        "exercise": "pistol_squat",
        "rep_count": genuine_reps,
        "checks": checks,
    }
