# Ascend

An RPG-style calisthenics progression app. Unlock skills by proving your form — upload a video, pass the automated analysis, earn the node.

## Demo

[![Ascend demo](https://img.youtube.com/vi/AfWIMEkXu8M/maxresdefault.jpg)](https://youtu.be/AfWIMEkXu8M)

## How it works

1. Browse the skill tree across four tracks: **Push**, **Pull**, **Core**, **Legs**
2. Click an unlockable skill to see what it requires and how to film yourself
3. Upload a video attempt — the backend runs pose estimation on every frame and checks your form against that skill's specific criteria
4. **Pass** → skill unlocks, your attempt becomes the showcase video on the node — proof it's been conquered. Re-attempt anytime to replace it with a cleaner rep.
5. **Fail** → structured feedback cards show exactly what to fix, try again

## Features

- **Skill tree UI** — RPG-style visual map with prerequisite chains, locked/unlockable/unlocked node states, and animated unlock feedback
- **Pose-based form analysis** — MediaPipe extracts joint coordinates from every video frame; angle calculations check bottom extension, top flexion, body alignment, and kipping for each exercise
- **Per-skill SVG icons** — 21 hand-drawn stick-figure icons, one per skill
- **Skeleton overlay** — after analysis, the MediaPipe landmark skeleton is drawn over your video in real time as it plays back
- **LLM coaching feedback** — Claude generates a short natural-language paragraph summarising the attempt alongside the structured pass/fail cards
- **Showcase replacement** — after any pass, you're prompted to save or skip the video. Come back and beat yourself to claim a cleaner showcase; the old file is deleted automatically.
- **User accounts** — Supabase auth; all progress and videos are tied to your account across sessions
- **Demo videos** — each skill node shows a demo clip before you attempt it

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | Python + FastAPI |
| Pose estimation | MediaPipe |
| LLM feedback | Claude API (Haiku 4.5) |
| Database + Auth | Supabase (PostgreSQL + Storage) |
| Frontend deployment | Vercel |
| Backend deployment | Railway |

## Running locally

**Prerequisites:** Node.js, Python 3.10+, a Supabase project

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env.local`:
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://127.0.0.1:8000
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Create `backend/.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
ANTHROPIC_API_KEY=your_anthropic_api_key
FRONTEND_URL=http://localhost:5173
```

## Project context

Built as a portfolio project in my first year studying Computer Science at UCL. I'm an advanced calisthenics practitioner — the domain knowledge directly shaped technical decisions, from the form check thresholds to the choice of which exercises to analyse first.

The DEVLOG in this repo documents every decision, bug, and concept learned throughout the build — written for interview preparation and personal reflection.
