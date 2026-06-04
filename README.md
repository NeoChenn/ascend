# Calisthenics Coach

An AI-powered web app that analyses calisthenics form from video and tracks skill progression.

## What it does

- **Video analysis** — upload a video of a pull-up or push-up and get automated form feedback using pose estimation
- **Skill tree** — visual progression map to track which skills you've achieved or are working towards
- **User accounts** — save your upload history and skill progress across sessions

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | Python + FastAPI |
| Pose estimation | MediaPipe |
| Database + Auth | Supabase |
| Frontend deployment | Vercel |
| Backend deployment | Railway / Render |

## Running locally

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Requires a `.env` file in `backend/` with your Supabase credentials (see `.env.example` when added).
