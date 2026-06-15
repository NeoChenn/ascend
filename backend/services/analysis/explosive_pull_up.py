from services.analysis._shared import _check_body_alignment
from services.analysis.pull_up import _check_bottom_extension, _detect_pullup_rep_phases


def _check_chest_to_bar(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
    top_frame_indices: list[int],
) -> dict:
    """
    Check that the chest (shoulders) reaches bar height at the top of the rep.

    In a standard pull-up, only the chin clears the bar. In an explosive pull-up,
    the athlete pulls hard enough to bring the chest to bar level — the shoulders
    should rise to the same height as the wrists (which are gripping the bar).

    In MediaPipe normalised coords, y increases downward, so a shoulder above the
    bar has a smaller y-value than the wrists. We compute:
      gap = avg_wrist_y - avg_shoulder_y
    Positive gap = shoulders above bar (pass). Negative = below bar (fail).
    """
    if not top_frame_indices:
        return {
            "name": "chest_to_bar",
            "passed": False,
            "message": "Could not detect a clear top position in your video.",
            "measurement": None,
        }

    gaps: list[float] = []

    for idx in top_frame_indices:
        if idx >= len(landmarks_per_frame):
            continue
        frame = landmarks_per_frame[idx]

        avg_shoulder_y = (frame["left_shoulder"]["y"] + frame["right_shoulder"]["y"]) / 2
        avg_wrist_y    = (frame["left_wrist"]["y"]    + frame["right_wrist"]["y"])    / 2

        gaps.append(avg_wrist_y - avg_shoulder_y)

    if not gaps:
        return {
            "name": "chest_to_bar",
            "passed": False,
            "message": "Could not assess chest height — shoulder or wrist landmarks were not visible.",
            "measurement": None,
        }

    avg_gap = sum(gaps) / len(gaps)
    # Tolerance of 0.05: the shoulder *joint* sits slightly below the sternum,
    # so when the chest genuinely touches the bar the shoulder landmark can
    # still read a small negative gap.
    passed = avg_gap >= -0.05

    if passed:
        message = "Chest reached bar level — great explosive height."
    else:
        message = (
            f"Shoulders were {abs(avg_gap):.2f} below bar height at the top. "
            "Pull explosively enough to bring your chest up to the bar."
        )

    return {
        "name": "chest_to_bar",
        "passed": passed,
        "message": message,
        "measurement": round(avg_gap, 3),
    }


def analyse_explosive_pull_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run all explosive pull-up form checks on the extracted per-frame landmark data.

    The defining characteristic of an explosive pull-up is pulling with enough force
    to bring the chest to bar level (not just the chin). We reuse standard pull-up
    rep detection and the bottom-extension check, then add a chest-to-bar height check
    in place of the chin-over-bar check used in the standard pull-up.

    No kipping check — explosive pull-ups intentionally use power and momentum.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "explosive_pull_up",
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

    # Smaller window for a short explosive rep — default 11 flattens a 1-second video
    phase_data = _detect_pullup_rep_phases(landmarks_per_frame, window=5)
    reps: list[tuple[int, int]] = phase_data["reps"]
    elbow_angles: list[float] = phase_data["elbow_angles"]

    first_rep = reps[0]
    bottom_frames = [first_rep[0]]
    top_frames = [first_rep[1]]

    genuine_reps = len(reps) if reps != [(0, len(landmarks_per_frame) - 1)] else 0

    checks = [
        _check_bottom_extension(elbow_angles, bottom_frames),
        _check_chest_to_bar(landmarks_per_frame, top_frames),
        _check_body_alignment(landmarks_per_frame),
    ]

    return {
        "exercise": "explosive_pull_up",
        "rep_count": genuine_reps,
        "checks": checks,
    }
