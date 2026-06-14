from services.analysis._shared import (
    _check_leg_straightness,
    _compute_hip_angles,
    _smooth_signal,
)
from services.analysis.leg_raise import _check_no_swing


def _detect_tob_rep_phases(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Identify the bottom and top of each toes-to-bar rep.

    Toes to bar is a stricter version of the leg raise — the legs must travel
    past horizontal all the way to the bar (a full pike). The top threshold is
    therefore much lower: < 60° instead of < 110°.

    Returns:
        {
          "reps": [(bottom_frame_idx, top_frame_idx), ...],
          "hip_angles": [float, ...]   # smoothed, one per frame
        }
    Falls back to [(0, last_frame)] if no reps are detected.
    """
    smoothed = _smooth_signal(_compute_hip_angles(landmarks_per_frame), window=11)

    bottom_indices: list[int] = []
    top_indices: list[int] = []

    for i in range(1, len(smoothed) - 1):
        is_local_max = smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]
        is_local_min = smoothed[i] < smoothed[i - 1] and smoothed[i] < smoothed[i + 1]

        # Bottom: legs hanging straight down
        if is_local_max and smoothed[i] > 160:
            bottom_indices.append(i)
        # Top: full pike — toes approaching or touching the bar
        if is_local_min and smoothed[i] < 60:
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

    return {"reps": reps, "hip_angles": smoothed}


def _check_tob_height(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the toes (ankles) actually reach the bar at the top of each rep.

    In MediaPipe normalised coords, y increases downward — so a landmark that is
    higher on screen has a smaller y value. The bar is at wrist height (the hands
    are gripping it), so we compare ankle y to wrist y at the top frames.

    Pass condition: average ankle y ≤ average wrist y (ankles at or above the bar).

    This is a positional check rather than an angle-based one — angle alone cannot
    answer "did the toes reach the bar?" because the bar position in frame varies.
    """
    if not top_frame_indices:
        return {
            "name": "toes_to_bar_height",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    gaps: list[float] = []

    for idx in top_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]

        # Use only visible side(s) — from side-on, the far ankle may be inaccurate.
        ankle_ys = [
            frame[k]["y"] for k in ["left_ankle", "right_ankle"]
            if frame[k]["visibility"] >= 0.5
        ] or [(frame["left_ankle"]["y"] + frame["right_ankle"]["y"]) / 2]
        wrist_ys = [
            frame[k]["y"] for k in ["left_wrist", "right_wrist"]
            if frame[k]["visibility"] >= 0.5
        ] or [(frame["left_wrist"]["y"] + frame["right_wrist"]["y"]) / 2]
        avg_ankle_y = sum(ankle_ys) / len(ankle_ys)
        avg_wrist_y = sum(wrist_ys) / len(wrist_ys)

        # Negative gap means ankles are above wrists (toes reached or passed the bar)
        gaps.append(avg_ankle_y - avg_wrist_y)

    if not gaps:
        return {
            "name": "toes_to_bar_height",
            "passed": False,
            "message": "Could not assess height — ankle or wrist landmarks were not visible.",
            "measurement": None,
        }

    avg_gap = sum(gaps) / len(gaps)
    # Pass if ankles are at or above wrist level (gap ≤ 0, with a small 0.05 tolerance)
    passed = avg_gap <= 0.05

    if passed:
        message = "Toes reached the bar — excellent range of motion."
    else:
        message = (
            f"Toes did not reach the bar (ankles were {avg_gap:.2f} below wrist level). "
            "Drive your hips up and pull your toes all the way to touch the bar."
        )

    return {
        "name": "toes_to_bar_height",
        "passed": passed,
        "message": message,
        "measurement": round(avg_gap, 3),
    }


def analyse_toes_to_bar(landmarks_per_frame: list[dict[str, dict[str, float]]]) -> dict:
    """
    Run all toes-to-bar form checks on the extracted per-frame landmark data.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "toes_to_bar",
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

    phase_data = _detect_tob_rep_phases(landmarks_per_frame)
    reps: list[tuple[int, int]] = phase_data["reps"]

    top_frames = [reps[0][1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_tob_height(landmarks_per_frame, top_frames),
        _check_leg_straightness(landmarks_per_frame, top_frames),
        _check_no_swing(landmarks_per_frame),
    ]

    return {
        "exercise": "toes_to_bar",
        "rep_count": genuine_reps,
        "checks": checks,
    }
