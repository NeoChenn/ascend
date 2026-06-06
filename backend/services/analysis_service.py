import math

import numpy as np


# --------------------------------------------------------------------------- #
# Core geometry helper
# --------------------------------------------------------------------------- #

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
    # Vectors from B toward A and from B toward C
    ba = (a["x"] - b["x"], a["y"] - b["y"])
    bc = (c["x"] - b["x"], c["y"] - b["y"])

    # Dot product: ba.x*bc.x + ba.y*bc.y
    dot_product = ba[0] * bc[0] + ba[1] * bc[1]

    # Magnitudes (lengths) of each vector
    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    # Guard against zero-length vectors (two identical landmarks)
    if magnitude_ba == 0 or magnitude_bc == 0:
        return 0.0

    # Clamp to [-1, 1] before arccos — floating-point arithmetic can produce
    # values like 1.0000000002 which would raise a math domain error.
    cos_angle = float(np.clip(dot_product / (magnitude_ba * magnitude_bc), -1.0, 1.0))

    return math.degrees(math.acos(cos_angle))


# --------------------------------------------------------------------------- #
# Signal smoothing
# --------------------------------------------------------------------------- #

def _smooth_signal(values: list[float], window: int = 5) -> list[float]:
    """
    Apply a simple moving average over `values` with a uniform window.

    Returns a list of the same length. Frames near the edges are averaged
    over fewer neighbours (numpy handles this automatically with mode='same').
    If the list is shorter than the window, return it unchanged — smoothing
    a tiny list would just distort it.
    """
    if len(values) < window:
        return values

    kernel = np.ones(window) / window  # uniform weights that sum to 1
    smoothed = np.convolve(values, kernel, mode="same")
    return smoothed.tolist()


# --------------------------------------------------------------------------- #
# Rep detection
# --------------------------------------------------------------------------- #

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


def _detect_pullup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each pull-up rep in the video.

    For a pull-up:
    - Bottom (arms straight, hanging) → elbow angle is near 180° → local MAX
    - Top (arms bent, chin over bar) → elbow angle is small (~60°) → local MIN

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "elbow_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame))

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: a local maximum above 150° (arms close to straight)
        if is_local_max and smoothed[i] > 150:
            bottom_indices.append(i)
        # Top: a local minimum below 110° (arms well bent, chin likely over bar)
        if is_local_min and smoothed[i] < 110:
            top_indices.append(i)

    # Pair each bottom with the next top that follows it in time
    reps: list[tuple[int, int]] = []
    for bottom_idx in bottom_indices:
        next_top = next((t for t in top_indices if t > bottom_idx), None)
        if next_top is not None:
            reps.append((bottom_idx, next_top))

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "elbow_angles": smoothed}


def _detect_pushup_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each push-up rep in the video.

    For a push-up, the elbow angle signal is the OPPOSITE of a pull-up:
    - Bottom (chest near floor, arms bent) → elbow angle is small (~70–90°) → local MIN
    - Top (arms extended, plank position) → elbow angle is near 180° → local MAX

    Returns the same shape as _detect_pullup_rep_phases.
    """
    smoothed = _smooth_signal(_compute_elbow_angles(landmarks_per_frame))

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: a local minimum below 100° (chest close to the floor)
        if is_local_min and smoothed[i] < 100:
            bottom_indices.append(i)
        # Top: a local maximum above 150° (arms close to fully extended)
        if is_local_max and smoothed[i] > 150:
            top_indices.append(i)

    # Pair each bottom with the next top that follows it in time (the "up" phase)
    reps: list[tuple[int, int]] = []
    for bottom_idx in bottom_indices:
        next_top = next((t for t in top_indices if t > bottom_idx), None)
        if next_top is not None:
            reps.append((bottom_idx, next_top))

    if not reps:
        reps = [(0, len(landmarks_per_frame) - 1)]

    return {"reps": reps, "elbow_angles": smoothed}


# --------------------------------------------------------------------------- #
# Individual form checks
# --------------------------------------------------------------------------- #

def _check_bottom_extension(
    elbow_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether arms are fully extended at the bottom of each rep.

    A fully straight arm has an elbow angle close to 180°. We use 160° as the
    threshold — anything below that means the athlete is not fully straightening
    between reps, which reduces range of motion and pulling strength development.
    """
    if not bottom_frame_indices:
        return {
            "name": "bottom_extension",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle > 160

    if passed:
        message = f"Good full extension at the bottom — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the bottom was only {avg_angle:.0f}° — "
            "try to fully straighten your arms between reps."
        )

    return {
        "name": "bottom_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_top_flexion(
    elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete pulls high enough at the top of each rep.

    An elbow angle below 90° at the top typically means the chin has cleared
    the bar. Above 90° usually means the rep is incomplete — chin has not made
    it over the bar.
    """
    if not top_frame_indices:
        return {
            "name": "top_flexion",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle < 90

    if passed:
        message = (
            f"Good height at the top — average elbow angle {avg_angle:.0f}°, "
            "chin is likely clearing the bar."
        )
    else:
        message = (
            f"Elbow angle at the top was {avg_angle:.0f}° — "
            "pull higher so your chin clears the bar."
        )

    return {
        "name": "top_flexion",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_body_alignment(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Check whether the body stays in a straight line throughout the movement.

    We measure the shoulder→hip→knee angle. A perfectly straight body gives 180°.
    Hip sag (the body bending forward at the hips) produces a smaller angle.
    We threshold at 160° — anything below that is noticeable sagging.

    We average the left and right sides and skip frames where any involved
    landmark has low visibility (< 0.5), since an occluded joint would give
    a meaningless angle.
    """
    valid_angles: list[float] = []

    for frame in landmarks_per_frame:
        # Check each side independently — when filming from the side, the far-side
        # joints are occluded and will have low visibility. Requiring ALL six joints
        # to be visible would discard almost every frame in a side-on video.
        left_visible = all(
            frame[j]["visibility"] >= 0.5
            for j in ["left_shoulder", "left_hip", "left_knee"]
        )
        right_visible = all(
            frame[j]["visibility"] >= 0.5
            for j in ["right_shoulder", "right_hip", "right_knee"]
        )

        if not left_visible and not right_visible:
            continue  # skip frames where neither side has reliable joints

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


def _check_kipping(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Check for kipping — using a hip swing to generate upward momentum.

    Kipping shows up as a sudden large upward jump in shoulder position between
    consecutive frames. In MediaPipe's coordinate system, y decreases as you
    move up, so a sudden *decrease* in shoulder y indicates a fast upward jerk.

    We measure the frame-to-frame change in average shoulder y. Legitimate
    pull-up shoulder movement is gradual. A change > 0.03 in a single frame
    (roughly 22 pixels in a 720p video) suggests kipping.
    """
    shoulder_y_values: list[float] = []

    for frame in landmarks_per_frame:
        avg_shoulder_y = (frame["left_shoulder"]["y"] + frame["right_shoulder"]["y"]) / 2
        shoulder_y_values.append(avg_shoulder_y)

    if len(shoulder_y_values) < 2:
        return {
            "name": "kipping",
            "passed": True,
            "message": "Not enough frames to assess kipping.",
            "measurement": None,
        }

    # Compute the absolute frame-to-frame delta in shoulder y position
    max_delta = max(
        abs(shoulder_y_values[i] - shoulder_y_values[i - 1])
        for i in range(1, len(shoulder_y_values))
    )
    passed = max_delta < 0.03

    if passed:
        message = "No kipping detected — movement looks controlled."
    else:
        message = (
            "Possible kipping detected — sudden upward shoulder movement suggests "
            "you may be using hip swing to generate momentum."
        )

    return {
        "name": "kipping",
        "passed": passed,
        "message": message,
        "measurement": round(max_delta, 4),
    }


# --------------------------------------------------------------------------- #
# Main analysis entry point
# --------------------------------------------------------------------------- #

def analyse_pull_up(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all pull-up form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    # Guard: not enough data to analyse
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "pull_up",
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

    # Detect rep phases (also gives us the smoothed elbow angle signal)
    phase_data = _detect_pullup_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    # Extract individual bottom and top frame indices from the rep list
    bottom_frames = [r[0] for r in reps]
    top_frames = [r[1] for r in reps]

    # Rep count: only count reps that were genuinely detected (not the fallback)
    # The fallback is [(0, last)] which means we couldn't find real rep cycles.
    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_bottom_extension(elbow_angles, bottom_frames),
        _check_top_flexion(elbow_angles, top_frames),
        _check_body_alignment(landmarks_per_frame),
        _check_kipping(landmarks_per_frame),
    ]

    return {
        "exercise": "pull_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }


# --------------------------------------------------------------------------- #
# Push-up form checks
# --------------------------------------------------------------------------- #

def _check_pushup_top_extension(
    elbow_angles: list[float],
    top_frame_indices: list[int],
) -> dict:
    """
    Check whether arms are fully extended at the top of each push-up rep.

    The top position is a full plank with locked-out elbows. We use 160° as the
    threshold — below that, the athlete is not pressing all the way up, which
    reduces tricep engagement and makes the top position structurally weak.
    """
    if not top_frame_indices:
        return {
            "name": "top_extension",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in top_frame_indices) / len(top_frame_indices)
    passed = avg_angle > 160

    if passed:
        message = f"Good lockout at the top — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the top was only {avg_angle:.0f}° — "
            "try to fully extend your arms at the top of each rep."
        )

    return {
        "name": "top_extension",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


def _check_pushup_bottom_depth(
    elbow_angles: list[float],
    bottom_frame_indices: list[int],
) -> dict:
    """
    Check whether the athlete lowers far enough on each rep (chest near floor).

    At full depth, the elbow angle is typically 70–90°. We use 100° as the
    threshold — above that, the chest is clearly not approaching the ground
    and the athlete is doing partial reps.
    """
    if not bottom_frame_indices:
        return {
            "name": "bottom_depth",
            "passed": False,
            "message": "Could not detect a clear bottom position in your video.",
            "measurement": None,
        }

    avg_angle = sum(elbow_angles[i] for i in bottom_frame_indices) / len(bottom_frame_indices)
    passed = avg_angle < 100

    if passed:
        message = f"Good depth at the bottom — average elbow angle {avg_angle:.0f}°."
    else:
        message = (
            f"Elbow angle at the bottom was {avg_angle:.0f}° — "
            "lower your chest closer to the ground for full range of motion."
        )

    return {
        "name": "bottom_depth",
        "passed": passed,
        "message": message,
        "measurement": round(avg_angle, 1),
    }


# --------------------------------------------------------------------------- #
# Push-up analysis entry point
# --------------------------------------------------------------------------- #

def analyse_push_up(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all push-up form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "push_up",
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

    phase_data = _detect_pushup_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    bottom_frames = [r[0] for r in reps]
    top_frames = [r[1] for r in reps]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_pushup_top_extension(elbow_angles, top_frames),
        _check_pushup_bottom_depth(elbow_angles, bottom_frames),
        _check_body_alignment(landmarks_per_frame),  # reused unchanged from pull-up
    ]

    return {
        "exercise": "push_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
