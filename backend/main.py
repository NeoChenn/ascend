from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
async def upload(file: UploadFile = File(...)):
    """
    Receives a video file, runs MediaPipe Pose on every frame,
    and returns the detected joint coordinates.

    File(...) is required to tell FastAPI to read from multipart form data
    rather than a JSON body, which is the default for POST requests.
    """
    print("Received file: " + file.filename)

    # Read the full file into memory as bytes, then pass to the pose service
    video_bytes = await file.read()
    pose_data = extract_landmarks_from_video(video_bytes)

    return {"filename": file.filename, **pose_data}