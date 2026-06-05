from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
    Receives a video file upload.
    File(...) is required to tell FastAPI to read from multipart form data
    rather than JSON body, which is the default for POST requests.
    """
    print("Received file: " + file.filename)
    return {"filename": file.filename}