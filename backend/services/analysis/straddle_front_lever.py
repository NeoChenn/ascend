import math

from services.analysis._shared import _compute_elbow_angles

_ASSUMED_FPS = 30
_MIN_HOLD_SECONDS = 3.0
_MIN_HOLD_FRAMES = int(_MIN_HOLD_SECONDS * _ASSUMED_FPS)  # 90 frames


def _compute_body_angle_from_horizontal(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> list[float]:
    """
    Compute the angle (degrees) that the shoulder→hip vector makes from horizontal,
    averaged over both sides, for every frame.

    In a front lever the body is parallel to the floor, so shoulder and hip are at
    the same height — the vector is approximately horizontal (angle ≈ 0°). Hanging
    straight down gives a vertical vector (angle ≈ 90°). Frames where landmarks are
    not visible default to 90° (worst case) so they never falsely count as passing.
    """
    per_frame_angles: list[float] = []

    for frame in landmarks_per_frame:
        side_angles: list[float] = []

        for shoulder_key, hip_key in [
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
        ]:
            shoulder = frame[shoulder_key]
            hip = frame[hip_key]

            if shoulder["visibility"] < 0.5 or hip["visibility"] < 0.5:
                continue

            dx = abs(hip["x"] - shoulder["x"])
            dy = abs(hip["y"] - shoulder["y"])

            if math.sqrt(dx**2 + dy**2) == 0:
                continue

            # atan2(dy, dx): 0° when dx >> dy (horizontal), 90° when dy >> dx (vertical)
            side_angles.append(math.degrees(math.atan2(dy, dx)))

        per_frame_angles.append(
            sum(side_angles) / len(side_angles) if side_angles else 90.0
        )

    return per_frame_angles


def _check_body_horizontal(body_angles: list[float]) -> dict:
    """
    Check that the body was held close to horizontal (averaged across all frames).

    Pass condition: average angle from horizontal < 25°. At 25° the body is clearly
    closer to flat than to vertical, which still represents a genuine front lever
    position (a 25° tilt from horizontal is within the acceptable range for a straddle
    variant where the legs change the centre of mass).
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


def _check_arm_lockout(elbow_angles: list[float]) -> dict:
    """
    Check that the arms remain straight throughout the front lever hold.

    Bending the elbows collapses the rigid support chain from hands to body. Pass: > 155°.
    Averaged across all frames because this is a static hold, not a rep.
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
            f"Average elbow angle was {avg_angle:.0f}° — straighten your arms fully. "
            "Bending the elbows causes the hips to drop and collapses the lever position."
        )

    return {
        "name": "arm_lockout",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def analyse_straddle_front_lever(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all straddle front lever form checks on the extracted per-frame landmark data.

    The straddle front lever is a static hold: the athlete hangs from a bar with the
    body horizontal, arms locked, and legs spread in a straddle. Like the L-sit, pass
    condition is a minimum consecutive hold duration during which the body is horizontal
    AND the arms are locked simultaneously. The straddle leg position itself is not
    checked — it cannot be distinguished from a full front lever from a side camera.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict with keys: exercise, rep_count, hold_seconds,
        checks: [{name, passed, message, measurement}, ...]
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "straddle_front_lever",
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

    # Per-frame pass: body horizontal AND arms locked simultaneously.
    per_frame_pass = [
        body_angle < 25 and elbow > 155
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
        hold_message = f"Held a clean straddle front lever for {hold_seconds}s — impressive!"
    else:
        hold_message = (
            f"Best clean hold was {hold_seconds}s — aim for {_MIN_HOLD_SECONDS:.0f}s. "
            "Body must be horizontal and arms locked simultaneously throughout."
        )

    checks = [
        _check_body_horizontal(body_angles),
        _check_arm_lockout(elbow_angles),
        {
            "name": "hold_duration",
            "passed": hold_passed,
            "message": hold_message,
            "measurement": hold_seconds,
        },
    ]

    return {
        "exercise": "straddle_front_lever",
        "rep_count": 0,
        "hold_seconds": hold_seconds,
        "checks": checks,
    }
