from services.analysis._shared import (
    _check_body_alignment,
    _smooth_signal,
    calculate_angle,
)
from services.analysis.pull_up import _check_bottom_extension


def _detect_archer_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each archer pull-up rep.

    In an archer pull-up, one arm (the working arm) does the primary pull while the
    other extends laterally. We track the MINIMUM of the left and right elbow angles
    per frame — the working arm is always more bent, so the minimum reliably captures
    the rep without needing to know which arm is working in advance.

    This is the same approach used in bulgarian_split_squat.py and pistol_squat.py
    for exercises where only one side drives the rep.

    Thresholds are identical to the standard pull-up:
    - Bottom: local MAX > 150° (both arms straight in dead hang)
    - Top: local MIN < 110° (working arm well bent)

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "left_elbow_angles": [float, ...],    # raw, per frame
          "right_elbow_angles": [float, ...],   # raw, per frame
          "min_elbow_smoothed": [float, ...],   # smoothed min, used for rep detection
        }
    Falls back to [(0, last_frame)] if no reps detected.
    """
    left_elbow_angles = [
        calculate_angle(f["left_shoulder"], f["left_elbow"], f["left_wrist"])
        for f in landmarks_per_frame
    ]
    right_elbow_angles = [
        calculate_angle(f["right_shoulder"], f["right_elbow"], f["right_wrist"])
        for f in landmarks_per_frame
    ]

    min_elbow_per_frame = [min(l, r) for l, r in zip(left_elbow_angles, right_elbow_angles)]
    smoothed = _smooth_signal(min_elbow_per_frame, window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        if is_local_max and smoothed[i] > 150:
            bottom_indices.append(i)
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

    return {
        "reps": reps,
        "left_elbow_angles": left_elbow_angles,
        "right_elbow_angles": right_elbow_angles,
        "min_elbow_smoothed": smoothed,
    }


def _check_working_arm_depth(
    left_elbow_angles: list[float],
    right_elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the working arm pulls deeply at the top of each rep.

    The working arm is whichever has the smaller elbow angle at the top frame —
    it is more bent because it is doing the primary pulling. Pass: < 90°, which
    is the equivalent of clearing the bar on a one-arm pull.
    """
    if not top_frame_indices:
        return {
            "name": "working_arm_depth",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    working_angles: list[float] = []

    for idx in top_frame_indices:
        if idx >= len(left_elbow_angles):
            continue
        working_angles.append(min(left_elbow_angles[idx], right_elbow_angles[idx]))

    if not working_angles:
        return {
            "name": "working_arm_depth",
            "passed": False,
            "message": "Could not assess working arm depth — elbow landmarks not visible at the top.",
            "measurement": None,
        }

    avg_angle = sum(working_angles) / len(working_angles)
    passed = avg_angle < 90

    if passed:
        message = f"Good working arm depth — elbow reached {avg_angle:.0f}° at the top."
    else:
        message = (
            f"Working arm elbow was {avg_angle:.0f}° at the top. "
            "Pull your working arm deeper — aim to get the elbow below 90°."
        )

    return {
        "name": "working_arm_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_assisting_arm_extension(
    left_elbow_angles: list[float],
    right_elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the assisting arm remains extended at the top of each rep.

    The archer pull-up requires the non-working arm to extend laterally throughout
    the movement. The assisting arm is whichever has the larger elbow angle at the
    top frame. Pass: > 140° (clearly extended, not tucked in like a standard pull-up).
    """
    if not top_frame_indices:
        return {
            "name": "assisting_arm_extension",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    assisting_angles: list[float] = []

    for idx in top_frame_indices:
        if idx >= len(left_elbow_angles):
            continue
        assisting_angles.append(max(left_elbow_angles[idx], right_elbow_angles[idx]))

    if not assisting_angles:
        return {
            "name": "assisting_arm_extension",
            "passed": False,
            "message": "Could not assess assisting arm — elbow landmarks not visible at the top.",
            "measurement": None,
        }

    avg_angle = sum(assisting_angles) / len(assisting_angles)
    passed = avg_angle > 140

    if passed:
        message = f"Good assisting arm extension — {avg_angle:.0f}° at the top."
    else:
        message = (
            f"Assisting arm was only {avg_angle:.0f}° at the top. "
            "Keep the assisting arm straighter — extend it out to the side rather than "
            "tucking it in like a standard pull-up."
        )

    return {
        "name": "assisting_arm_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_archer_pull_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all archer pull-up form checks on the extracted per-frame landmark data.

    An archer pull-up is a single-arm pull-up progression: one arm (the working arm)
    does the primary pulling while the other (the assisting arm) extends laterally to
    provide partial assistance. The key checks are that the working arm pulls deeply
    and the assisting arm stays extended — the two criteria that distinguish an archer
    pull-up from a plain asymmetric pull-up.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "archer_pull_up",
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

    phase_data = _detect_archer_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    left_elbow_angles: list[float] = phase_data["left_elbow_angles"]
    right_elbow_angles: list[float] = phase_data["right_elbow_angles"]
    min_elbow_smoothed: list[float] = phase_data["min_elbow_smoothed"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        # Pass smoothed min-elbow signal to _check_bottom_extension — at the dead hang
        # both arms are extended, so the minimum still reads close to 180°.
        _check_bottom_extension(min_elbow_smoothed, bottom_frames),
        _check_working_arm_depth(left_elbow_angles, right_elbow_angles, top_frames),
        _check_assisting_arm_extension(left_elbow_angles, right_elbow_angles, top_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "archer_pull_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
