from services.analysis._shared import (
    _check_body_alignment,
    _smooth_signal,
    calculate_angle,
)
from services.analysis.push_up import _check_pushup_top_extension


def _detect_archer_pushup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each archer push-up rep.

    In an archer push-up, one arm (the working arm) bears most of the load while
    the other extends laterally. We track the MINIMUM of left and right elbow angles
    per frame — the working arm (more bent) always produces the smaller angle, so the
    minimum reliably captures the rep.

    Push-up signal direction is the OPPOSITE of pull-up:
    - Bottom (chest near floor): elbow angle is small → local MIN < 100°
    - Top (arms extended): elbow angle is large → local MAX > 150°

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

        # Bottom: chest near floor, working arm bent
        if is_local_min and smoothed[i] < 100:
            bottom_indices.append(i)
        # Top: arms extended
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
        "left_elbow_angles": left_elbow_angles,
        "right_elbow_angles": right_elbow_angles,
        "min_elbow_smoothed": smoothed,
    }


def _check_working_arm_depth(
    left_elbow_angles: list[float],
    right_elbow_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check that the working arm reaches a deep bend at the bottom of each rep.

    The working arm is whichever has the smaller elbow angle at the bottom frame.
    Pass: < 80° — stricter than a standard push-up (< 100°) to confirm the athlete
    is genuinely loading one arm, not just doing a slightly asymmetric push-up.
    """
    if not bottom_frame_indices:
        return {
            "name": "working_arm_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    working_angles: list[float] = []

    for idx in bottom_frame_indices:
        if idx >= len(left_elbow_angles):
            continue
        working_angles.append(min(left_elbow_angles[idx], right_elbow_angles[idx]))

    if not working_angles:
        return {
            "name": "working_arm_depth",
            "passed": False,
            "message": "Could not assess working arm depth — elbow landmarks not visible at the bottom.",
            "measurement": None,
        }

    avg_angle = sum(working_angles) / len(working_angles)
    passed = avg_angle < 80

    if passed:
        message = f"Good working arm depth — elbow reached {avg_angle:.0f}° at the bottom."
    else:
        message = (
            f"Working arm elbow was {avg_angle:.0f}° at the bottom. "
            "Lower your chest further — aim to bend the working arm below 80°."
        )

    return {
        "name": "working_arm_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }



def analyse_archer_push_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all archer push-up form checks on the extracted per-frame landmark data.

    An archer push-up is a one-arm push-up progression: one arm (the working arm)
    bears most of the load while the other arm extends laterally (the assisting arm).
    The key checks are that the working arm bends deeply and the assisting arm stays
    extended — the same criteria that distinguish an archer pull-up from a plain
    asymmetric pull-up.

    Rep detection uses min(left, right) elbow angle per frame — the working arm is
    always more bent, so the minimum tracks the rep without requiring advance knowledge
    of which arm is working. This is the same approach used in archer_pull_up.py.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "archer_push_up",
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

    phase_data = _detect_archer_pushup_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    left_elbow_angles: list[float] = phase_data["left_elbow_angles"]
    right_elbow_angles: list[float] = phase_data["right_elbow_angles"]
    min_elbow_smoothed: list[float] = phase_data["min_elbow_smoothed"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_working_arm_depth(left_elbow_angles, right_elbow_angles, bottom_frames),
        # Pass smoothed min-elbow to top_extension — at the top both arms are near 180°
        # so the minimum still reads close to 180° and the check is valid.
        _check_pushup_top_extension(min_elbow_smoothed, top_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "archer_push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
