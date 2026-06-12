import os

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.analysis import (
    analyse_bulgarian_split_squat,
    analyse_pistol_squat,
    analyse_pull_up,
    analyse_push_up,
    analyse_squat,
)
from services.llm_service import generate_narrative_feedback
from services.pose_service import extract_landmarks_from_video

# Maps the exercise value sent by the frontend to the correct analyser function.
# Add new exercises here as they are implemented — no other code needs to change.
ANALYSERS = {
    "pull_up": analyse_pull_up,
    "push_up": analyse_push_up,
    "squat": analyse_squat,
    "bulgarian_split_squat": analyse_bulgarian_split_squat,
    "pistol_squat": analyse_pistol_squat,
}

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), exercise: str = Form(...)):
    """
    Receives a video file and an exercise type, runs MediaPipe Pose on every
    frame, then runs form analysis for the specified exercise.

    Both `file` and `exercise` are sent as multipart form data fields.
    File(...) and Form(...) tell FastAPI to read from form data rather than a
    JSON body, which is the default for POST requests.

    exercise must match a key in ANALYSERS (e.g. "pull_up", "squat").
    Skills with no analyser yet return null feedback and null narrative.
    """
    print(f"Received file: {file.filename} (exercise: {exercise})")

    video_bytes = await file.read()
    pose_data = extract_landmarks_from_video(video_bytes)

    analyser = ANALYSERS.get(exercise)
    if analyser:
        feedback = analyser(pose_data["landmarks_per_frame"])
        # Narrative is generated after analysis so the checks array is already available.
        # Returns None on failure — the frontend handles both cases gracefully.
        narrative = generate_narrative_feedback(exercise, feedback["checks"])
    else:
        feedback = None
        narrative = None

    return {"filename": file.filename, **pose_data, "feedback": feedback, "narrative": narrative}