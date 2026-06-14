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

    Two separate signals are used, for the same reason as Bulgarian split squat:
      - Bottom detection: min(left, right) — the working leg is most bent at the
        bottom, so the minimum reliably finds the deepest point.
      - Top detection: max(left, right) — at the top the working leg extends to
        ~160°. The free leg may hang at ~100–130° between reps, which would drag
        min(L,R) below 150° and prevent top detection. max(L,R) always picks up
        the extended working leg regardless of what the free leg does.

    Returns:
        {
          "reps":           [(bottom_frame_idx, top_frame_idx), ...],
          "left_angles":    [float, ...],   # raw, one per frame
          "right_angles":   [float, ...],   # raw, one per frame
          "min_angles":     [float, ...]    # smoothed min(L,R) — used for depth check
          "max_angles":     [float, ...]    # smoothed max(L,R) — used for lockout check
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

    min_smoothed = _smooth_signal(
        [min(l, r) for l, r in zip(left_angles, right_angles)], window=11
    )
    max_smoothed = _smooth_signal(
        [max(l, r) for l, r in zip(left_angles, right_angles)], window=11
    )

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(min_smoothed) - 1):
        is_local_min = min_smoothed[i] < min_smoothed[i - 1] and min_smoothed[i] < min_smoothed[i + 1]
        is_local_max = max_smoothed[i] > max_smoothed[i - 1] and max_smoothed[i] > max_smoothed[i + 1]

        # Pistol squat requires deep knee flexion — stricter than a regular squat
        if is_local_min and min_smoothed[i] < 80:
            bottom_indices.append(i)
        if is_local_max and max_smoothed[i] > 150:
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
        "min_angles": min_smoothed,
        "max_angles": max_smoothed,
    }


def _check_pistol_depth(
    min_angles: list[float],
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

    avg_angle = sum(min_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
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
    max_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the working leg fully extends at the top of each rep.

    Uses max(L,R) angles so the working leg's extension is measured directly,
    regardless of what the free leg does between reps.
    Standing tall on one leg with a locked knee should produce an angle above 155°.
    """
    if not top_frame_indices:
        return {
            "name": "pistol_lockout",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(max_angles[i] for i in top_frame_indices) / len(top_frame_indices)
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
    working_leg: str,
) -> dict:
    """
    Check that the free leg stays extended throughout the movement.

    Evaluated over all frames where the free leg landmarks are clearly visible
    AND the working knee is above 100° (not near the bottom of the squat).

    At the deepest point, the free knee passes behind the working leg from the
    side-on camera angle — MediaPipe predicts a plausible but wrong position
    with medium confidence, bypassing the visibility gate. Skipping frames where
    the working knee is below 100° avoids this occlusion zone entirely, and
    evaluating the free leg during the descent, ascent, and standing phases gives
    an accurate picture of whether it stayed straight throughout.
    """
    free_leg = "right" if working_leg == "left" else "left"
    hip_key = f"{free_leg}_hip"
    knee_key = f"{free_leg}_knee"
    ankle_key = f"{free_leg}_ankle"
    work_hip_key = f"{working_leg}_hip"
    work_knee_key = f"{working_leg}_knee"
    work_ankle_key = f"{working_leg}_ankle"

    angles: list[float] = []

    for frame in landmarks_per_frame:
        # Skip the deep zone where the free knee is hidden behind the working leg
        if all(frame[k]["visibility"] >= 0.5 for k in [work_hip_key, work_knee_key, work_ankle_key]):
            working_angle = calculate_angle(
                frame[work_hip_key], frame[work_knee_key], frame[work_ankle_key]
            )
            if working_angle < 100:
                continue

        if any(frame[k]["visibility"] < 0.5 for k in [hip_key, knee_key, ankle_key]):
            continue

        angles.append(calculate_angle(frame[hip_key], frame[knee_key], frame[ankle_key]))

    if not angles:
        return {
            "name": "free_leg_extension",
            "passed": True,
            "message": (
                "Free leg not clearly visible outside the bottom position — "
                "check passed by default."
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
    min_angles: list[float] = phase_data["min_angles"]
    max_angles: list[float] = phase_data["max_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    working_leg = _identify_working_leg(landmarks_per_frame, bottom_frames)
    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_pistol_depth(min_angles, bottom_frames),
        _check_pistol_lockout(max_angles, top_frames),
        _check_pistol_free_leg(landmarks_per_frame, working_leg),
    ]

    return {
        "exercise": "pistol_squat",
        "rep_count": genuine_reps,
        "checks": checks,
    }
