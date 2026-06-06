import os
import tempfile
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# The lite model is fast and accurate enough for form analysis.
# It is downloaded automatically on first use and cached at this path.
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task")
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)

# The landmark indices we care about for pull-up and push-up analysis.
# MediaPipe detects 33 points total; we only extract these 10.
# Full list: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
LANDMARK_NAMES: dict[int, str] = {
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
}


def _ensure_model() -> None:
    """Download the pose landmarker model file if it isn't already cached."""
    if not os.path.exists(_MODEL_PATH):
        print("Downloading MediaPipe pose model (first run only)...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("Model downloaded.")


def extract_landmarks_from_video(video_bytes: bytes) -> dict:
    """
    Runs MediaPipe Pose on every frame of the provided video.

    Args:
        video_bytes: Raw bytes of the uploaded video file.

    Returns:
        A dict with:
          - frame_count: how many frames had a detected pose
          - landmarks_per_frame: list of dicts, one per frame,
            each mapping joint name → {x, y, z, visibility}
    """
    _ensure_model()

    # OpenCV cannot read video from raw bytes — it needs a file path.
    # We write to a temporary file, process it, then delete it.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    landmarks_per_frame = []

    try:
        base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)

        # VIDEO mode tracks joints across frames rather than re-detecting
        # from scratch each time — faster and more stable than IMAGE mode.
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        cap = cv2.VideoCapture(tmp_path)

        # Compute timestamps from frame index + FPS rather than
        # cap.get(CAP_PROP_POS_MSEC), which can be unreliable for some codecs.
        # Some video codecs don't store FPS metadata, causing cap.get(cv2.CAP_PROP_FPS)
        #  to return 0.0. "or 30.0" falls back to 30 FPS as a sensible default
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_index = 0

        with mp_vision.PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                timestamp_ms = int((frame_index / fps) * 1000)
                frame_index += 1

                # OpenCV reads frames as BGR; MediaPipe expects RGB.
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                result = landmarker.detect_for_video(mp_image, timestamp_ms)

                # pose_landmarks is an empty list if no person was detected
                if not result.pose_landmarks:
                    continue

                # result.pose_landmarks is a list of detected people (we cap at 1)
                pose = result.pose_landmarks[0]

                frame_landmarks: dict[str, dict] = {}
                for index, name in LANDMARK_NAMES.items():
                    lm = pose[index]
                    frame_landmarks[name] = {
                        "x": lm.x,
                        "y": lm.y,
                        "z": lm.z,
                        "visibility": lm.visibility,
                    }

                landmarks_per_frame.append(frame_landmarks)

        cap.release()

    finally:
        # Always clean up the temp file, even if an error occurred
        os.unlink(tmp_path)

    return {
        "frame_count": len(landmarks_per_frame),
        "landmarks_per_frame": landmarks_per_frame,
    }
