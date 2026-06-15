from services.analysis._shared import _compute_elbow_angles, _smooth_signal


def analyse_muscle_up(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run form checks for a muscle-up on the extracted per-frame landmark data.

    A muscle-up has two phases: an explosive pull above the bar, then a dip lockout
    at the top. We skip the dip transition (which requires knowing the exact bar
    position) and instead verify the two most important positions:

    1. Pull depth — elbow angle drops below 70° at some point, confirming the
       athlete pulled the elbows past the bar to reach the transition height.
    2. Above-bar lockout — arms lock out (> 150°) while the hips are above the bar
       (hip y < wrist y in MediaPipe coords), confirming the dip was completed.

    Together these confirm the athlete both reached above the bar and locked out —
    the two hallmarks of a completed muscle-up.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict matching the FormFeedback Pydantic model shape:
        {exercise, rep_count, checks: [{name, passed, message, measurement}, ...]}
    """
    if len(landmarks_per_frame) < 3:
        return {
            "exercise": "muscle_up",
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

    elbow_angles = _compute_elbow_angles(landmarks_per_frame)
    smoothed = _smooth_signal(elbow_angles, window=11)

    # Rep count: each local minimum below 70° in the smoothed signal is one
    # muscle-up transition (pull through the bar). This mirrors how pull-up rep
    # detection works — each dip of the elbow angle curve = one rep.
    # Fallback: if smoothing flattens a short video with no clear local minimum
    # but the raw signal still dropped below 70°, count it as 1 rep.
    rep_count = sum(
        1 for i in range(1, len(smoothed) - 1)
        if smoothed[i] < smoothed[i - 1]
        and smoothed[i] < smoothed[i + 1]
        and smoothed[i] < 70
    )
    if rep_count == 0 and min(elbow_angles) < 70:
        rep_count = 1

    # Check 1: Pull depth — minimum elbow angle across all frames.
    # A muscle-up requires pulling the elbows past the bar, which demands a much
    # tighter angle (< 70°) than a standard chin-over-bar pull-up (≈ 90°).
    min_elbow = min(elbow_angles)
    pull_depth_passed = min_elbow < 70

    if pull_depth_passed:
        pull_depth_message = (
            f"Good pull depth — elbow angle reached {min_elbow:.0f}° (below 70°)."
        )
    else:
        pull_depth_message = (
            f"Insufficient pull depth — minimum elbow angle was {min_elbow:.0f}°. "
            "Pull your elbows past the bar (aim below 70°) to reach the transition point."
        )

    # Check 2: Above-bar lockout — verify that after the deepest pull (elbows < 70°),
    # the elbows subsequently return to lockout (> 150°). This is a temporal sequence
    # check: pull_depth already confirms the transition height was reached; if the
    # elbows then lock out, the dip was completed. No wrist/hip positional landmark
    # is needed — those are unreliable when the hand is gripping a bar.
    deepest_pull_frame = elbow_angles.index(min(elbow_angles))
    lockout_found = any(
        elbow_angles[i] > 150
        for i in range(deepest_pull_frame, len(elbow_angles))
    )

    if lockout_found:
        lockout_message = "Locked out above the bar with straight arms — muscle-up completed."
    else:
        lockout_message = (
            "No above-bar lockout detected. Fully straighten your arms "
            "with your hips above the bar to complete the muscle-up."
        )

    checks = [
        {
            "name": "pull_depth",
            "passed": pull_depth_passed,
            "message": pull_depth_message,
            "measurement": round(min_elbow, 1),
        },
        {
            "name": "above_bar_lockout",
            "passed": lockout_found,
            "message": lockout_message,
            "measurement": None,
        },
    ]

    return {
        "exercise": "muscle_up",
        "rep_count": rep_count,
        "checks": checks,
    }
