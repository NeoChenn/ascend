from services.analysis.straddle_front_lever import analyse_straddle_front_lever


def analyse_straddle_planche(
    landmarks_per_frame: list[dict[str, dict[str, float]]],
) -> dict:
    """
    Run form checks for a straddle planche.

    From a side camera, the straddle planche and straddle front lever are geometrically
    identical: body horizontal, arms straight. MediaPipe cannot distinguish floor/parallette
    support (planche) from bar support (front lever) — both appear as the same landmark
    configuration. All analysis logic is therefore reused directly from
    straddle_front_lever.py; only the exercise name in the return dict changes.

    Args:
        landmarks_per_frame: Output of extract_landmarks_from_video — a list of
            dicts, one per frame, each mapping joint name to {x, y, z, visibility}.

    Returns:
        A dict with keys: exercise, rep_count, hold_seconds,
        checks: [{name, passed, message, measurement}, ...]
    """
    result = analyse_straddle_front_lever(landmarks_per_frame)
    result["exercise"] = "straddle_planche"
    return result
