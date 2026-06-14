from services.analysis._shared import (
    _check_body_alignment,
    _compute_elbow_angles,
    _smooth_signal,
)


def _detect_hsp_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify extended (lockout) and flexed (head near floor) frames for each
    handstand push-up rep.

    After the vertical flip, a handstand push-up looks like an overhead press:
      - Extended frame = local MAX of elbow angle (arms locked out at top)
      - Flexed frame   = local MIN of elbow angle (head near floor)

    The lockout threshold is 120° rather than the pull-up equivalent (150°)
    because HSPu lockout may not reach full extension if shoulder mobility is
    limited, or if the video starts partway through a rep.
    """
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame), window=11)

    extended_indices: list[int] = []
    flexed_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        if is_local_max and smoothed[i] > 120:
            extended_indices.append(i)
        if is_local_min and smoothed[i] < 110:
            flexed_indices.append(i)

    all_events: list[tuple[int, str]] = sorted(
        [(idx, "extended") for idx in extended_indices] +
        [(idx, "flexed") for idx in flexed_indices]
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
        if deduped[i][1] == "extended" and deduped[i + 1][1] == "flexed"
    ]

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {
        "reps": reps,
        "elbow_angles": smoothed,
    }


def _check_hsp_lockout(
    elbow_angles: list[float],
    extended_frame_indices: list[int],
) -> dict:
    """
    Check that the elbows are fully extended at the top of the handstand push-up.

    After the vertical flip, lockout corresponds to the pull-up 'bottom' frame
    (local angle maximum). Threshold is 150° — slightly more lenient than a
    pull-up dead hang because overhead lockout can be limited by shoulder mobility.
    """
    if not extended_frame_indices:
        return {
            "name": "lockout",
            "passed": False,
            "message": "Could not detect the lockout position — ensure your full rep is visible.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in extended_frame_indices) / len(extended_frame_indices)
    passed = avg_angle > 140

    if passed:
        message = f"Good lockout — elbows were {avg_angle:.0f}° at the top of the press."
    else:
        message = (
            f"Elbow angle at the top was {avg_angle:.0f}° — "
            "fully press to arm extension at the top of each rep."
        )

    return {
        "name": "lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_hsp_depth(
    elbow_angles: list[float],
    flexed_frame_indices: list[int],
) -> dict:
    """
    Check that the head lowers close to the floor at the bottom of the press.

    On a flat floor, head-to-floor clearance limits elbow flexion to roughly
    80–95°. A threshold of < 100° is used rather than the pull-up equivalent
    (< 90°) to account for this physical constraint.
    """
    if not flexed_frame_indices:
        return {
            "name": "depth",
            "passed": False,
            "message": "Could not detect the bottom position — ensure your full rep is visible.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in flexed_frame_indices) / len(flexed_frame_indices)
    passed = avg_angle < 100

    if passed:
        message = f"Good depth — elbows reached {avg_angle:.0f}° at the bottom of the press."
    else:
        message = (
            f"Elbow angle at the bottom was {avg_angle:.0f}° — "
            "lower your head closer to the floor for full range of motion."
        )

    return {
        "name": "depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_handstand_push_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all handstand push-up form checks on the extracted per-frame landmark data.

    The video is submitted normally (floor at the bottom). The backend flips it
    vertically before MediaPipe runs (flip_vertical=True in pose_service.py), so the
    model sees an upright person with arms raised overhead. In the flipped view, a
    handstand push-up looks exactly like a pull-up: the person starts with arms
    extended (elbows ~170°), bends them until the head approaches the floor
    (elbows ~90°), then extends back.

    We therefore reuse _detect_pullup_rep_phases directly:
      - local MAX > 150° → "bottom" frame = arms extended = lockout position
      - local MIN < 110° → "top" frame   = arms flexed  = head near floor

    Only the first detected rep is evaluated (first-rep-only policy shared by all
    dynamic analysers — prevents penalising a clean rep for a weaker follow-up).

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video (with flip_vertical=True
            applied upstream in pose_service.py) — a list of dicts, one per frame, each
            mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "handstand_push_up",
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

    phase_data = _detect_hsp_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    first_rep = reps[0]
    extended_frames = [first_rep[0]]  # lockout position
    flexed_frames = [first_rep[1]]    # head near floor

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_hsp_lockout(elbow_angles, extended_frames),
        _check_hsp_depth(elbow_angles, flexed_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "handstand_push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
