from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.analysis import analyse_pull_up, analyse_push_up
from services.llm_service import generate_narrative_feedback
from services.pose_service import extract_landmarks_from_video

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

    exercise must be one of: "pull_up", "push_up"
    """
    print(f"Received file: {file.filename} (exercise: {exercise})")

    video_bytes = await file.read()
    pose_data = extract_landmarks_from_video(video_bytes)

    if exercise == "push_up":
        feedback = analyse_push_up(pose_data["landmarks_per_frame"])
    else:
        feedback = analyse_pull_up(pose_data["landmarks_per_frame"])

    # Narrative is generated after analysis so the checks array is already available.
    # Returns None on failure — the frontend handles both cases gracefully.
    narrative = generate_narrative_feedback(exercise, feedback["checks"])

    return {"filename": file.filename, **pose_data, "feedback": feedback, "narrative": narrative}