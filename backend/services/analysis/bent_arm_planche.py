from services.analysis._shared import _compute_elbow_angles
from services.analysis.straddle_front_lever import _compute_body_angle_from_horizontal

_ASSUMED_FPS = 30
_MIN_HOLD_SECONDS = 3.0
_MIN_HOLD_FRAMES = int(_MIN_HOLD_SECONDS * _ASSUMED_FPS)  # 90 frames


def _check_planche_body_horizontal(body_angles: list[float]) -> dict:
    """
    Check that the body was held close to horizontal (averaged across all frames).

    Reuses the same 25° threshold as straddle_front_lever — the planche position
    demands the same horizontal body line, just with floor support instead of bar.
    """
    if not body_angles:
        return {
            "name": "body_horizontal",
            "passed": False,
            "message": "Could not assess body angle — shoulder or hip landmarks were not visible.",
            "measurement": None,
        }

    avg_angle = sum(body_angles) / len(body_angles)
    passed = avg_angle < 25

    if passed:
        message = f"Good horizontal position — body was {avg_angle:.0f}° from horizontal on average."
    else:
        message = (
            f"Body was {avg_angle:.0f}° from horizontal on average. "
            "Keep your hips up — the body must be parallel to the floor throughout the hold."
        )

    return {
        "name": "body_horizontal",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_arms_bent(elbow_angles: list[float]) -> dict:
    """
    Check that the arms remain bent throughout the hold.

    The bent arm planche is specifically a bent-arm position — if the elbows drift
    toward straight the hold becomes a straddle planche, a different and harder skill.
    Pass condition: average elbow angle < 110°, confirming the arms are clearly bent.
    """
    if not elbow_angles:
        return {
            "name": "arm_bent",
            "passed": False,
            "message": "Could not assess arm angle — elbow landmarks were not visible.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles) / len(elbow_angles)
    passed = avg_angle < 110

    if passed:
        message = f"Good bent-arm position — average elbow angle was {avg_angle:.0f}°."
    else:
        message = (
            f"Average elbow angle was {avg_angle:.0f}° — keep your arms bent throughout. "
            "Straightening the arms converts this into a straddle planche."
        )

    return {
        "name": "arm_bent",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_bent_arm_planche(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all bent arm planche form checks on the extracted per-frame landmark data.

    The bent arm planche is a static hold where the body is parallel to the floor
    supported by bent arms, hands near the hips. It is the entry-point planche
    progression — building the wrist loading, shoulder depression, and forward lean
    the full planche demands. Like the L-sit and straddle front lever, pass condition
    is a minimum consecutive hold duration during which all criteria are simultaneously
    met.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict with keys: exercise, rep_count, hold_seconds,
        checks: [{name, passed, message, measurement}, ...]
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "bent_arm_planche",
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
    body_angles = _compute_body_angle_from_horizontal(landmarks_per_frame)

    # Per-frame pass: body horizontal AND arms bent simultaneously.
    per_frame_pass = [
        body_angle < 25 and elbow < 110
        for body_angle, elbow in zip(body_angles, elbow_angles)
    ]

    # Longest consecutive run of passing frames.
    max_streak = current = 0
    for frame_passed in per_frame_pass:
        current = current + 1 if frame_passed else 0
        if current > max_streak:
            max_streak = current

    hold_seconds = round(max_streak / _ASSUMED_FPS, 1)
    hold_passed = max_streak >= _MIN_HOLD_FRAMES

    if hold_passed:
        hold_message = f"Held a clean bent arm planche for {hold_seconds}s — well done!"
    else:
        hold_message = (
            f"Best clean hold was {hold_seconds}s — aim for {_MIN_HOLD_SECONDS:.0f}s. "
            "Body must be horizontal and arms bent simultaneously throughout."
        )

    checks = [
        _check_planche_body_horizontal(body_angles),
        _check_arms_bent(elbow_angles),
        {
            "name": "hold_duration",
            "passed": hold_passed,
            "message": hold_message,
            "measurement": hold_seconds,
        },
    ]

    return {
        "exercise": "bent_arm_planche",
        "rep_count": 0,
        "hold_seconds": hold_seconds,
        "checks": checks,
    }
