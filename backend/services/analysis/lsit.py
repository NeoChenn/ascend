from services.analysis._shared import (
    _compute_elbow_angles,
    _compute_hip_angles,
    _compute_knee_angles,
)


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

    The L-sit is a static hold, not a rep-based movement. There is no rep detection
    phase — all checks average across the entire video to assess whether the position
    is maintained throughout the hold. rep_count is always 0.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count: 0, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "lsit",
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

    # No phase detection — average across the full hold
    hip_angles = _compute_hip_angles(landmarks_per_frame)
    knee_angles = _compute_knee_angles(landmarks_per_frame)
    elbow_angles = _compute_elbow_angles(landmarks_per_frame)

    checks = [
        _check_lsit_hip_angle(hip_angles),
        _check_lsit_leg_extension(knee_angles),
        _check_lsit_arm_lockout(elbow_angles),
    ]

    return {
        "exercise": "lsit",
        "rep_count": 0,
        "checks": checks,
    }
