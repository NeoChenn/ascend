import math

import numpy as np



def calculate_angle(
    a: dict[str, float],
    b: dict[str, float],
    c: dict[str, float],
) -> float:
    """
    Return the angle (in degrees) at joint B, given three landmark dicts.

    Each dict must have 'x' and 'y' keys (normalised screen coords from MediaPipe).
    B is the vertex — e.g. pass shoulder→elbow→wrist to get the elbow angle.

    How it works:
      1. Build two vectors that both start at B and point toward A and C.
      2. Use the dot-product formula: cos(angle) = (BA · BC) / (|BA| * |BC|)
      3. Invert with arccos to get the angle, then convert to degrees.
    """
    ba = (a["x"] - b["x"], a["y"] - b["y"])
    bc = (c["x"] - b["x"], c["y"] - b["y"])

    dot_product = ba[0] * bc[0] + ba[1] * bc[1]

    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    if magnitude_ba == 0 or magnitude_bc == 0:
        return 0.0

    # Clamp to [-1, 1] before arccos — floating-point arithmetic can produce
    # values like 1.0000000002 which would raise a math domain error.
    cos_angle = float(np.clip(dot_product / (magnitude_ba * magnitude_bc), -1.0, 1.0))

    return math.degrees(math.acos(cos_angle))


def _smooth_signal(values: list[float], window: int = 5) -> list[float]:
    """
    Apply a simple moving average over `values` with a uniform window.

    Returns a list of the same length. Frames near the edges are averaged
    over fewer neighbours (numpy handles this automatically with mode='same').
    If the list is shorter than the window, return it unchanged.
    """
    if len(values) < window:
        return values

    kernel = np.ones(window) / window
    smoothed = np.convolve(values, kernel, mode="same")
    return smoothed.tolist()


def _compute_elbow_angles(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> list[float]:
    """
    Compute the average left+right elbow angle for every frame.

    We average both sides because the camera may be side-on (one arm hidden)
    or front-facing (both visible). Averaging keeps the signal reasonable
    in either case, since MediaPipe often mirrors occluded joints.
    """
    angles: list[float] = []
    for frame in landmarks_per_frame:
        left_angle = calculate_angle(
            frame["left_shoulder"], frame["left_elbow"], frame["left_wrist"]
        )
        right_angle = calculate_angle(
            frame["right_shoulder"], frame["right_elbow"], frame["right_wrist"]
        )
        angles.append((left_angle + right_angle) / 2)
    return angles


def _check_body_alignment(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Check whether the body stays in a straight line throughout the movement.

    We measure the shoulder→hip→knee angle. A perfectly straight body gives 180°.
    Hip sag (the body bending forward at the hips) produces a smaller angle.
    We threshold at 160° — anything below that is noticeable sagging.

    We check each side independently — when filming from the side, the far-side
    joints are occluded and will have low visibility. Requiring ALL six joints
    to be visible would discard almost every frame in a side-on video.
    """
    valid_angles: list[float] = []

    for frame in landmarks_per_frame:
        left_visible = all(
            frame[j]["visibility"] >= 0.5
            for j in ["left_shoulder", "left_hip", "left_knee"]
        )
        right_visible = all(
            frame[j]["visibility"] >= 0.5
            for j in ["right_shoulder", "right_hip", "right_knee"]
        )

        if not left_visible and not right_visible:
            continue

        side_angles: list[float] = []
        if left_visible:
            side_angles.append(calculate_angle(
                frame["left_shoulder"], frame["left_hip"], frame["left_knee"]
            ))
        if right_visible:
            side_angles.append(calculate_angle(
                frame["right_shoulder"], frame["right_hip"], frame["right_knee"]
            ))

        valid_angles.append(sum(side_angles) / len(side_angles))

    if not valid_angles:
        return {
            "name": "body_alignment",
            "passed": False,
            "message": "Could not assess body alignment — hip or knee landmarks were not clearly visible.",
            "measurement": None,
        }

    avg_angle = sum(valid_angles) / len(valid_angles)
    passed = avg_angle > 160

    if passed:
        message = f"Good body alignment — hips stayed relatively straight (avg {avg_angle:.0f}°)."
    else:
        message = (
            f"Average body alignment was {avg_angle:.0f}° — your hips may be sagging. "
            "Try to keep your body in a straight line throughout the movement."
        )

    return {
        "name": "body_alignment",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _compute_knee_angles(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> list[float]:
    """
    Compute the average left+right knee angle (hip-knee-ankle) for every frame.

    Averaging both sides handles side-on cameras where one leg may be occluded;
    MediaPipe mirrors joints so both sides produce a reasonable signal.

    Landmark indices used (MediaPipe):
      Left:  hip (23) → knee (25) → ankle (27)
      Right: hip (24) → knee (26) → ankle (28)
    """
    angles: list[float] = []
    for frame in landmarks_per_frame:
        left_angle = calculate_angle(
            frame["left_hip"], frame["left_knee"], frame["left_ankle"]
        )
        right_angle = calculate_angle(
            frame["right_hip"], frame["right_knee"], frame["right_ankle"]
        )
        angles.append((left_angle + right_angle) / 2)
    return angles


def _check_torso_upright(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check that the torso stays within ~45° of vertical at the bottom of a squat.

    We measure the angle between the shoulder→hip vector and a true vertical
    reference. This is different from _check_body_alignment, which measures hip
    sag in a plank — here we're measuring forward lean in a standing movement.

    We only check at the bottom frames because that is where forward lean is worst.

    In MediaPipe normalised coords, y increases downward, so the torso vector from
    hip to shoulder has a negative y-component (shoulder sits at a smaller y than hip).
    The lean angle is computed with atan2(horizontal_displacement, vertical_displacement).
    """
    lean_angles: list[float] = []

    for idx in bottom_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]

        for shoulder_key, hip_key in [
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
        ]:
            shoulder = frame[shoulder_key]
            hip = frame[hip_key]

            if shoulder["visibility"] < 0.5 or hip["visibility"] < 0.5:
                continue

            dx = shoulder["x"] - hip["x"]
            dy = shoulder["y"] - hip["y"]  # negative: shoulder is above hip

            if math.sqrt(dx**2 + dy**2) == 0:
                continue

            # Angle from vertical = arctan(horizontal / vertical component)
            lean_angle = math.degrees(math.atan2(abs(dx), abs(dy)))
            lean_angles.append(lean_angle)

    if not lean_angles:
        return {
            "name": "torso_upright",
            "passed": False,
            "message": (
                "Could not assess torso angle — shoulder or hip landmarks "
                "were not clearly visible at the bottom position."
            ),
            "measurement": None,
        }

    avg_lean = sum(lean_angles) / len(lean_angles)
    passed = avg_lean < 45

    if passed:
        message = f"Good torso position — forward lean at the bottom was {avg_lean:.0f}°."
    else:
        message = (
            f"Torso was leaning {avg_lean:.0f}° forward at the bottom. "
            "Try to keep your chest up — this often indicates tight ankles or hips."
        )

    return {
        "name": "torso_upright",
        "passed": passed,
        "message": message,
        "measurement": round(avg_lean, 1),
    }
