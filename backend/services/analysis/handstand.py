from services.analysis._shared import (
    _check_body_alignment,
    _compute_elbow_angles,
    calculate_angle,
)

_ASSUMED_FPS = 30
_MIN_HOLD_SECONDS = 3.0
_MIN_HOLD_FRAMES = int(_MIN_HOLD_SECONDS * _ASSUMED_FPS)  # 90 frames


def _compute_body_alignment_angles(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> list[float]:
    """
    Compute the shoulder→hip→knee angle per frame.

    Returns one float per frame. When no joints are sufficiently visible,
    defaults to 90° so that a frame with missing landmarks never counts as
    passing the body-straight criterion.
    """
    angles: list[float] = []
    for frame in landmarks_per_frame:
        side_angles: list[float] = []
        for shoulder_key, hip_key, knee_key in [
            ("left_shoulder", "left_hip", "left_knee"),
            ("right_shoulder", "right_hip", "right_knee"),
        ]:
            if all(frame[j]["visibility"] >= 0.5 for j in [shoulder_key, hip_key, knee_key]):
                side_angles.append(
                    calculate_angle(frame[shoulder_key], frame[hip_key], frame[knee_key])
                )
        angles.append(sum(side_angles) / len(side_angles) if side_angles else 90.0)
    return angles


def _check_handstand_arm_lockout(elbow_angles: list[float]) -> dict:
    """
    Check that the arms remain straight throughout the handstand hold.

    In a clean handstand, elbows are locked to ~180°. An average above 155°
    indicates adequate lockout. Bent elbows collapse the support and waste energy.
    """
    if not elbow_angles:
        return {
            "name": "arm_lockout",
            "passed": False,
            "message": "Could not assess arm lockout — elbow landmarks were not visible.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles) / len(elbow_angles)
    passed = avg_angle > 155

    if passed:
        message = f"Good arm lockout — average elbow angle was {avg_angle:.0f}°."
    else:
        message = (
            f"Average elbow angle was {avg_angle:.0f}° — keep your arms fully locked out. "
            "Bent elbows during a handstand waste energy and collapse the base."
        )

    return {
        "name": "arm_lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_handstand(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all handstand form checks on the extracted per-frame landmark data.

    The video is submitted normally (floor at the bottom). The backend flips it
    vertically before MediaPipe runs (flip_vertical=True in pose_service.py), so
    the model sees an upright person with arms raised overhead — standard coordinates.
    No remapping is needed here; all angle checks work unchanged.

    The handstand is a static hold. Pass condition: a minimum consecutive streak of
    _MIN_HOLD_SECONDS during which both body alignment AND arm lockout criteria are
    simultaneously met. Both diagnostic cards are returned regardless so the user
    can see which criterion is causing them to fail.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video (with flip_vertical=True
            applied upstream in pose_service.py) — a list of dicts, one per frame, each
            mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict with keys: exercise, rep_count, hold_seconds,
        checks: [{name, passed, message, measurement}, ...]
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "handstand",
            "rep_count": 0,
            "hold_seconds": 0.0,
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

    elbow_angles = _compute_elbow_angles(landmarks_per_frame)
    body_angles = _compute_body_alignment_angles(landmarks_per_frame)

    # Per-frame: both criteria must pass simultaneously.
    # body > 155° = shoulder-hip-knee acceptably straight (allows slight natural arch).
    # elbow > 155° = arms locked out.
    per_frame_pass = [
        body > 155 and elbow > 155
        for body, elbow in zip(body_angles, elbow_angles)
    ]

    # Find the longest consecutive run of fully-passing frames.
    max_streak = current = 0
    for frame_passed in per_frame_pass:
        current = current + 1 if frame_passed else 0
        if current > max_streak:
            max_streak = current

    hold_seconds = round(max_streak / _ASSUMED_FPS, 1)
    hold_passed = max_streak >= _MIN_HOLD_FRAMES

    if hold_passed:
        hold_message = f"Held a clean handstand for {hold_seconds}s — well done!"
    else:
        hold_message = (
            f"Best clean hold was {hold_seconds}s — aim for {_MIN_HOLD_SECONDS:.0f}s. "
            "Both body alignment and arm lockout must be maintained simultaneously."
        )

    checks = [
        _check_body_alignment(landmarks_per_frame),
        _check_handstand_arm_lockout(elbow_angles),
        {
            "name": "hold_duration",
            "passed": hold_passed,
            "message": hold_message,
            "measurement": hold_seconds,
        },
    ]

    return {
        "exercise": "handstand",
        "rep_count": 0,
        "hold_seconds": hold_seconds,
        "checks": checks,
    }
