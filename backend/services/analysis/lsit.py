from services.analysis._shared import (
    _compute_elbow_angles,
    _compute_hip_angles,
    _compute_knee_angles,
)

_ASSUMED_FPS = 30
_MIN_HOLD_SECONDS = 3.0
_MIN_HOLD_FRAMES = int(_MIN_HOLD_SECONDS * _ASSUMED_FPS)  # 90 frames


def _check_lsit_hip_angle(hip_angles: list[float]) -> dict:
    """
    Check that the legs are held at or above horizontal throughout the hold.

    A shoulder-hip-ankle angle below 100° means the legs are at or above horizontal
    (90° = exactly horizontal). If the hips drop and the legs sag below horizontal,
    the angle rises above 100°.

    We average across all frames because the L-sit is a static hold — the position
    should be maintained, not just achieved momentarily.
    """
    if not hip_angles:
        return {
            "name": "lsit_hip_angle",
            "passed": False,
            "message": "Could not assess leg position — hip or ankle landmarks were not visible.",
            "measurement": None,
        }

    avg_angle = sum(hip_angles) / len(hip_angles)
    passed = avg_angle < 100

    if passed:
        message = f"Good L-sit position — average leg height was {avg_angle:.0f}° (legs horizontal or above)."
    else:
        message = (
            f"Average hip angle was {avg_angle:.0f}° — your legs are dropping below horizontal. "
            "Aim to hold your legs parallel to the floor or above throughout the hold."
        )

    return {
        "name": "lsit_hip_angle",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_lsit_leg_extension(knee_angles: list[float]) -> dict:
    """
    Check that the knees remain locked out throughout the hold.

    An L-sit requires straight legs — a knee angle above 155° indicates the legs
    are adequately extended. Bending the knees makes the hold significantly easier
    and disqualifies it as a true L-sit.
    """
    if not knee_angles:
        return {
            "name": "lsit_leg_extension",
            "passed": False,
            "message": "Could not assess leg extension — knee landmarks were not visible.",
            "measurement": None,
        }

    avg_angle = sum(knee_angles) / len(knee_angles)
    passed = avg_angle > 155

    if passed:
        message = f"Good leg extension — average knee angle was {avg_angle:.0f}°."
    else:
        message = (
            f"Average knee angle was {avg_angle:.0f}° — keep your legs fully straight "
            "throughout the hold. Bent knees disqualify the movement as a true L-sit."
        )

    return {
        "name": "lsit_leg_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_lsit_arm_lockout(elbow_angles: list[float]) -> dict:
    """
    Check that the arms remain straight and locked out throughout the hold.

    An L-sit requires the arms to be fully extended, depressing the shoulders to
    elevate the hips. An elbow angle above 155° indicates adequate lockout. Bent
    elbows collapse the support base and cause the hips to drop.
    """
    if not elbow_angles:
        return {
            "name": "lsit_arm_lockout",
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
            f"Average elbow angle was {avg_angle:.0f}° — straighten your arms fully. "
            "Locked elbows are required to create the rigid support base for the L-sit."
        )

    return {
        "name": "lsit_arm_lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_lsit(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all L-sit form checks on the extracted per-frame landmark data.

    The L-sit is a static hold, not a rep-based movement. Pass condition is a
    minimum consecutive hold duration (_MIN_HOLD_SECONDS) during which all three
    form criteria are simultaneously met. The three diagnostic cards (hip angle,
    leg extension, arm lockout) are still returned so the user knows which criterion
    is causing them to fail. rep_count is always 0; hold_seconds is returned instead.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict with keys: exercise, rep_count, hold_seconds,
        checks: [{name, passed, message, measurement}, ...]
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "lsit",
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

    hip_angles = _compute_hip_angles(landmarks_per_frame)
    knee_angles = _compute_knee_angles(landmarks_per_frame)
    elbow_angles = _compute_elbow_angles(landmarks_per_frame)

    # Per-frame: are ALL three criteria met simultaneously?
    # Hip < 100° = legs at or above horizontal.
    # Knee > 155° = legs straight, not tucked.
    # Elbow > 155° = arms locked out.
    per_frame_pass = [
        h < 100 and k > 155 and e > 155
        for h, k, e in zip(hip_angles, knee_angles, elbow_angles)
    ]

    # Find the longest consecutive run of passing frames.
    # A momentary correct position does not count — the hold must be sustained.
    max_streak = current = 0
    for frame_passed in per_frame_pass:
        current = current + 1 if frame_passed else 0
        if current > max_streak:
            max_streak = current

    hold_seconds = round(max_streak / _ASSUMED_FPS, 1)
    hold_passed = max_streak >= _MIN_HOLD_FRAMES

    if hold_passed:
        hold_message = f"Held a clean L-sit for {hold_seconds}s — well done!"
    else:
        hold_message = (
            f"Best clean hold was {hold_seconds}s — aim for {_MIN_HOLD_SECONDS:.0f}s. "
            "All three criteria (legs horizontal, knees straight, arms locked) "
            "must be met simultaneously throughout."
        )

    checks = [
        _check_lsit_hip_angle(hip_angles),
        _check_lsit_leg_extension(knee_angles),
        _check_lsit_arm_lockout(elbow_angles),
        {
            "name": "hold_duration",
            "passed": hold_passed,
            "message": hold_message,
            "measurement": hold_seconds,
        },
    ]

    return {
        "exercise": "lsit",
        "rep_count": 0,
        "hold_seconds": hold_seconds,
        "checks": checks,
    }
