# Calisthenics Coach — Dev Log

A running journal of progress, decisions, and learnings. Kept for interview preparation and personal reflection.

---

## How to use this file

At the end of each week, add a new entry with:
- **What I built** — concrete features or progress
- **What broke / what was hard** — real problems encountered
- **What I learned** — new concepts or technologies
- **Decisions made** — why you chose one approach over another
- **What's next** — what you're tackling next week

Keep it honest. The struggles are as important as the wins — interviewers respect candidates who can talk about problems they hit and how they solved them.

---

## Step 1 — Environment setup + React refresher

### What I built
- Scaffolded React app with Vite
- Set up three-page layout with React Router: Home, Upload, SkillTree
- Created GitHub repo and made first commits

### What I learned
- Refreshed React fundamentals: components, props, useState, React Router
- Set up a proper project structure separating frontend and backend from the start

### Decisions made
- **React + Vite over Create React App** — Vite is faster and more modern, better for development experience
- **Separated frontend and backend into distinct folders** — clean separation of concerns, mirrors how real production projects are structured
- **CSS Modules for styling** — scoped styles per component, avoids class name conflicts as the project grows

### What's next
- FastAPI basics
- Connect React frontend to Python backend

---

## Step 2 — FastAPI basics + frontend/backend connection

### What I built
- Set up FastAPI with a Python virtual environment
- Built a GET endpoint returning a basic JSON response
- Built a POST `/upload` endpoint that receives a video file
- Added CORS middleware so the frontend can talk to the backend without this the browser silently blocks cross-origin requests
- Connected React frontend to the backend — user selects a file, uploads it, filename displays on screen

### What broke / what was hard
- **422 Unprocessable Content error** — hit this when testing in Swagger without actually attaching a file. Learned that `File(...)` means the field is required and FastAPI returns 422 if it's missing.
- **Couldn't find the backend print output** — the upload form was returning the filename correctly in the frontend, so I thought everything was working — but I couldn't find the backend `print()` output anywhere in the browser DevTools console. It turned out the backend doesn't log there at all; it logs to the terminal window where `uvicorn` is running, because the frontend and backend are completely separate processes. Once I knew to look in the right place, the output was there.

### What I learned
- How HTTP request body types differ: JSON vs multipart form data
- Why `File(...)` is needed — tells FastAPI to read from form data rather than JSON body, which is the default for POST requests
- `UploadFile` attributes — `file.filename`, `file.content_type` etc.
- `FormData` in JavaScript — how it packages files for multipart requests
- Why you don't set `Content-Type` manually when using FormData — fetch detects it automatically
- Swagger UI as a tool for testing API endpoints without needing a frontend
- Backend print() appears in the terminal window where uvicorn is running, as opposed to frontend console.log, which appears in the browser DevTools console. They are completely separate processes with separate output streams.

### Decisions made
- **FastAPI over Django/Flask** — lightweight, modern, Python-native. Built-in Swagger docs are genuinely useful for testing. Type hints and Pydantic validation feel natural coming from a typed language background.
- **Virtual environment for backend** — isolates dependencies, standard professional practice

### What's next
- MediaPipe pose estimation
- Get landmark coordinates working on a static image in isolation before integrating with FastAPI

---

## Step 3 — MediaPipe pose estimation + pipeline integration

### What I built
- Integrated MediaPipe Pose into the `/upload` endpoint — the backend now runs pose estimation on every frame of an uploaded video and returns joint coordinates as JSON
- Created `backend/services/pose_service.py` to keep all MediaPipe logic separate from the route handler
- Created `backend/models/pose_models.py` with Pydantic models (`Landmark`, `PoseResult`) to define the shape of the response data
- Created `backend/requirements.txt` to document all backend dependencies
- Verified the full pipeline end-to-end: upload a video → backend extracts landmarks → JSON response with per-frame joint data

### What broke / what was hard
- **`mp.solutions` no longer exists in MediaPipe 0.10+** — every tutorial online uses the old API (`mp.solutions.pose`), but the installed version (0.10.35) has removed it entirely. Had to switch to the new Tasks API (`mediapipe.tasks.vision.PoseLandmarker`), which works differently and requires downloading a separate model file.
- **The new API requires a model file** — unlike the old API which bundled the model, the new Tasks API needs a `.task` file downloaded separately. Added auto-download on first run so it's seamless.

### What I learned

**What MediaPipe Pose is:**
MediaPipe is a library by Google that runs pre-trained machine learning models. The Pose model detects 33 points on a human body (called **landmarks**) from an image or video frame — things like left shoulder, right elbow, left hip, etc. Each landmark gives you four numbers:
- `x`, `y` — position on screen as a fraction (0.0 = left/top edge, 1.0 = right/bottom edge)
- `z` — depth relative to the hips (less reliable, mostly ignored for now)
- `visibility` — how confident MediaPipe is that the joint is visible (0.0–1.0)

**How video processing works:**
Video is just a sequence of images (frames). The library used to decode those frames is **OpenCV** (`cv2`). The flow is:
```
Video file → OpenCV reads frame by frame → Each frame is an image (NumPy array)
→ MediaPipe Pose analyses the image → Returns 33 landmark positions
→ We pick the 10 joints we care about → Return as JSON
```
One important gotcha: OpenCV reads images in **BGR** colour order (Blue, Green, Red), but MediaPipe expects **RGB**. You must convert between them with `cv2.cvtColor`, otherwise detection quality drops.

**The 10 landmarks extracted (sufficient for pull-up and push-up analysis):**
```
11: left shoulder    12: right shoulder
13: left elbow       14: right elbow
15: left wrist       16: right wrist
23: left hip         24: right hip
25: left knee        26: right knee
```

**What Pydantic models are for:**
Pydantic models describe the shape of data using Python classes. Without them, endpoints return plain dicts and nothing checks whether the types are correct. With a Pydantic model, FastAPI: (1) validates that the response matches the declared shape, (2) auto-documents the response structure in Swagger, and (3) serialises Python objects to clean JSON. Think of it as a contract — you're declaring "this endpoint always returns data that looks exactly like this."

### Decisions made
- **Tasks API over legacy `mp.solutions`** — the legacy API is removed in 0.10+, so there was no choice. The Tasks API is also the officially supported path going forward.
- **Lite model over full/heavy** — the lite model is fast enough for real-time-ish processing and accurate enough for form analysis. The heavy model would give marginally better landmark accuracy but with significantly slower inference.
- **VIDEO mode over IMAGE mode** — `RunningMode.VIDEO` tracks joints across frames rather than re-detecting from scratch each time, which is faster and more stable for continuous motion like pull-ups.
- **Computed timestamps over `CAP_PROP_POS_MSEC`** — VIDEO mode requires strictly increasing timestamps. `cap.get(CAP_PROP_POS_MSEC)` can be unreliable for some codecs, so timestamps are computed from frame index and FPS instead.

### What's next
- Angle-based form analysis for pull-ups (shoulder–elbow–wrist angle, body alignment)
- Return structured feedback alongside the landmark data

---

## Step 4 — Video upload + pose extraction pipeline

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Fill this in -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- Fill this in -->

### What's next
<!-- Fill this in -->

---

## Step 5 — Form analysis logic (pull-up)
*Date: Mid July 2026*

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Fill this in -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- How did you define "good form" thresholds? Why those specific angles? -->
<!-- This is where your domain expertise matters — document your reasoning -->

### What's next
<!-- Fill this in -->

---

## Ste`p 6 — Form analysis (push-up) + feedback UI
*Date: Late July 2026*

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Fill this in -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- Fill this in -->

### What's next
<!-- Fill this in -->

---

## Step 7 — Supabase + user accounts
*Date: Early August 2026*

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Fill this in -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- Why Supabase over building auth from scratch? -->
<!-- What did you store in the database and why? -->

### What's next
<!-- Fill this in -->

---

## Step 8 — Skill tree
*Date: Mid August 2026*

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Fill this in -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- How did you structure the skill progression data? -->
<!-- Why did you choose those specific exercises for the tree? -->
<!-- This is where your calisthenics domain knowledge is a differentiator — document it -->

### What's next
<!-- Fill this in -->

---

## Step 9 — Deployment + polish
*Date: Late August 2026*

### What I built
<!-- Fill this in -->

### What broke / what was hard
<!-- Deployment almost always has surprises — document them here -->
<!-- CORS issues in production? Environment variables? Cold start times? -->

### What I learned
<!-- Fill this in -->

### Decisions made
<!-- Why Vercel for frontend? Why Railway/Render for backend? -->
<!-- Any trade-offs with free tier limitations? -->

### What's next
<!-- Stretch goals if time allows -->

---

## Step 10 — Buffer + stretch goals
*Date: Early September 2026*

### What I built
<!-- Fill this in -->

### Stretch goals attempted
<!-- LLM feedback via Claude API? Skeleton overlay? Third exercise? -->

### Reflection
<!-- Looking back at the whole project:
- What are you most proud of technically?
- What would you do differently?
- What was the hardest problem you solved?
- How did your calisthenics knowledge directly shape technical decisions?
These are all interview questions — answer them here while it's fresh -->

---

## Key technical decisions (running list)

Keep this section updated as you make significant decisions. These are gold in interviews.

| Decision | Alternatives considered | Why I chose this |
|---|---|---|
| React + Vite for frontend | Create React App, Next.js | Faster dev server, simpler setup for a SPA |
| FastAPI for backend | Flask, Django | Lightweight, async-native, built-in Swagger, Python |
| MediaPipe for pose estimation | OpenPose, custom model | No model training required, free, well documented |
| Supabase for database + auth | Firebase, building auth from scratch | Managed Postgres + built-in auth saves significant time |
| Video upload over real-time webcam | Real-time webcam | Simpler to implement, better video quality for analysis |
| Vercel for frontend deployment | Netlify, GitHub Pages | Free, seamless GitHub integration, instant deploys |
| Railway/Render for backend | AWS, Heroku | Free tier, simple Python deployment |

---

## Problems solved (running list)

Keep a log of significant bugs or problems and how you solved them. Interviewers love these stories.

| Problem | Cause | Solution |
|---|---|---|
| 422 Unprocessable Content on file upload | No file attached when testing in Swagger | Attach file before executing in Swagger UI |
| Swagger showing no file input | Missing File and UploadFile imports | Added to fastapi import statement |
| Plain HTML form causing page navigation | Default browser form submission behaviour | Used e.preventDefault() and fetch with FormData instead |

---

*Started: June 2026*
*Target completion: Early September 2026*
