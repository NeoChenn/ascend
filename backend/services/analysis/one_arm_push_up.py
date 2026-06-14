from services.analysis._shared import (
    _smooth_signal,
    calculate_angle,
)


def _detect_onearm_pushup_frames(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Find the most extended (top) and most bent (bottom) frames in a one-arm push-up.

    Elbow angle is NOT used as the rep signal here. When filming from the side,
    a vertically-extended arm appears as a nearly collinear shoulder→elbow→wrist in
    2D, but MediaPipe often places the elbow slightly offset in x, collapsing the
    computed angle from the expected ~170° down to ~95–110°. This makes the elbow
    signal unreliable for detecting the lockout position.

    Instead we track wrist_y - shoulder_y (the vertical distance from shoulder to
    wrist in normalised frame coordinates). This is robust because:
      - TOP (arm extended, shoulder high): wrist_y >> shoulder_y → large value
      - BOTTOM (shoulder dropped toward floor): wrist_y ≈ shoulder_y → small value
    We take max(left, right) per frame so the working arm (wrist further from shoulder)
    always dominates, regardless of which side is being used.

    Returns:
        {
          "top_frame": int,       # frame where arm is most extended
          "bottom_frame": int,    # frame where arm is most bent
          "signal_range": float,  # how much the wrist-shoulder distance changed
        }
    """
    left_dist = [
        f["left_wrist"]["y"] - f["left_shoulder"]["y"]
        for f in landmarks_per_frame
    ]
    right_dist = [
        f["right_wrist"]["y"] - f["right_shoulder"]["y"]
        for f in landmarks_per_frame
    ]

    dist_signal = _smooth_signal(
        [max(l, r) for l, r in zip(left_dist, right_dist)],
        window=7,
    )

    max_dist = max(dist_signal)
    min_dist = min(dist_signal)

    return {
        "top_frame": dist_signal.index(max_dist),
        "bottom_frame": dist_signal.index(min_dist),
        "signal_range": max_dist - min_dist,
    }


def _check_onearm_top_extension(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    top_frame_idx: int,
) -> dict:
    """
    Check that the working arm is reasonably extended at the top of the push.

    We use the frame identified by the wrist-shoulder distance signal (the most
    extended moment), then read the max(left, right) elbow angle at that specific
    frame. Because MediaPipe underestimates the elbow angle from a pure side-on
    view (the elbow is placed slightly offset in x, reducing the computed angle),
    the threshold is set at 110° rather than the bilateral push-up's 160°.

    An elbow angle of 110° at the true top frame means the arm is meaningfully
    extended and the push has a genuine lockout, even if MediaPipe cannot resolve
    the full ~170° from this angle.
    """
    frame = landmarks_per_frame[top_frame_idx]
    left_angle = calculate_angle(
        frame["left_shoulder"], frame["left_elbow"], frame["left_wrist"]
    )
    right_angle = calculate_angle(
        frame["right_shoulder"], frame["right_elbow"], frame["right_wrist"]
    )
    angle = max(left_angle, right_angle)
    passed = angle > 110

    if passed:
        message = (
            f"Good lockout — elbow reached {angle:.0f}° at the top of the push."
        )
    else:
        message = (
            f"Elbow angle at the top was only {angle:.0f}° — "
            "try to fully extend your arm at the top of each rep."
        )

    return {
        "name": "top_extension",
        "passed": passed,
        "message": message,
        "measurement": round(angle, 1),
    }


def _check_onearm_bottom_depth(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    bottom_frame_idx: int,
) -> dict:
    """
    Check that the working arm bends sufficiently at the bottom of the push.

    At the bottom frame (identified by the wrist-shoulder distance signal, when
    the shoulder has dropped closest to the floor), we check min(left, right) elbow
    angle. The working arm is the more bent one, so the minimum reliably picks it up.
    Threshold: < 90°, confirming the chest approached the floor.
    """
    frame = landmarks_per_frame[bottom_frame_idx]
    left_angle = calculate_angle(
        frame["left_shoulder"], frame["left_elbow"], frame["left_wrist"]
    )
    right_angle = calculate_angle(
        frame["right_shoulder"], frame["right_elbow"], frame["right_wrist"]
    )
    angle = min(left_angle, right_angle)
    passed = angle < 90

    if passed:
        message = f"Good depth — elbow reached {angle:.0f}° at the bottom."
    else:
        message = (
            f"Elbow angle at the bottom was {angle:.0f}° — "
            "lower your chest closer to the ground for full range of motion."
        )

    return {
        "name": "bottom_depth",
        "passed": passed,
        "message": message,
        "measurement": round(angle, 1),
    }


def _check_onearm_body_alignment(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Check body alignment for a one-arm push-up.

    Threshold is 140° rather than the standard 160° — a wider leg stance is
    required for balance when only one hand is on the floor, which naturally
    reduces the shoulder-hip-knee angle without indicating poor form.
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
    passed = avg_angle > 140

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


def analyse_one_arm_push_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run form checks for a one-arm push-up.

    Rep detection uses wrist-shoulder vertical distance rather than elbow angles,
    because MediaPipe systematically underestimates elbow angle from a pure side-on
    view of a vertical arm. The distance signal reliably tracks the top/bottom of the
    rep without depending on accurate elbow placement.

    Form checks are evaluated at the specific top/bottom frames identified by the
    distance signal, with adjusted thresholds that account for the side-on view:
      - top_extension:   > 110° (vs 160° for bilateral)
      - bottom_depth:    < 90°
      - body_alignment:  > 140° (vs 160°, accounts for wider leg stance)

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "one_arm_push_up",
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

    frame_data = _detect_onearm_pushup_frames(landmarks_per_frame)
    top_frame = frame_data["top_frame"]
    bottom_frame = frame_data["bottom_frame"]
    signal_range = frame_data["signal_range"]

    # A meaningful range of motion (>2% of normalised frame height) means we
    # detected a genuine rep, not just a static hold or a noisy flatline.
    rep_count = 1 if signal_range > 0.02 else 0

    checks = [
        _check_onearm_top_extension(landmarks_per_frame, top_frame),
        _check_onearm_bottom_depth(landmarks_per_frame, bottom_frame),
        _check_onearm_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "one_arm_push_up",
        "rep_count": rep_count,
        "checks": checks,
    }
