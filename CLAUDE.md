# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Ascend

## Commands

**Frontend** (from `frontend/`):
```bash
npm run dev        # start Vite dev server
npm run build      # production build
npm run lint       # ESLint
```

**Backend** (from `backend/`):
```bash
uvicorn main:app --reload   # start FastAPI dev server
pip install -r requirements.txt
pytest                       # run tests
pytest tests/test_foo.py     # run a single test file
```

## Project overview

An RPG-style calisthenics progression app. The skill tree is the core of the app — users browse skills organised into tracks (push, pull, legs, core), pick one they want to unlock, upload a video attempting it, and receive automated form analysis against that skill's specific criteria. Pass → skill unlocked, video saved to their profile. Fail → feedback shown, try again.

Each skill node displays a demo video (filmed by the developer) until the user unlocks it, at which point their own unlock video replaces it and becomes permanently rewatchable on the node.

This is a personal project built for my CV as a first-year CS student at UCL. It should be complete, deployed, and demonstrable to recruiters.

## My background

- First year CS student at UCL
- Comfortable with Python and basic frontend (HTML, CSS, JavaScript, some React)
- New to FastAPI, backend development in general, MediaPipe, and Supabase
- Familiar with DSA concepts from university but not with applying them in production code
- Advanced calisthenics practitioner — I have strong domain knowledge of the exercises being analysed

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | Python + FastAPI |
| Pose estimation | MediaPipe |
| Database + Auth | Supabase (PostgreSQL) |
| Frontend deployment | Vercel |
| Backend deployment | Railway or Render |
| LLM feedback | Claude API |

## Current build status

**Done:**
- Video upload + MediaPipe pose extraction
- Pull-up and push-up form analysis (angle-based, structured feedback cards)
- Supabase: schema (4 tables), RLS policies, storage buckets (demo-videos, unlock-videos)
- Auth: login, signup, session persistence via AuthContext
- Muscle map skill tree landing page (interactive SVG at /skill-tree)
- Track pages at /track/:trackId — column-based skill tree with real Supabase data, locked/unlockable/unlocked states, H-branch SVG connectors
- SkillNode component (3 visual states) + SkillModal (skill info, filming instructions, disabled upload button)

**Next:**
- Skill-specific upload flow: wire SkillModal "Upload attempt" button to backend form analysis
- Pass/fail result → write to user_skills + skill_attempts in Supabase
- Skill node updates to unlocked state after successful upload

## Project structure (current)

```
calisthenics-coach/
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.jsx        # session state, useAuth() hook
│   │   ├── pages/
│   │   │   ├── Home.jsx               # landing page
│   │   │   ├── SkillTree.jsx          # muscle map — navigates to track pages
│   │   │   ├── TrackPage.jsx          # skill nodes for one track (/track/:trackId)
│   │   │   ├── Upload.jsx             # legacy generic upload (to be replaced)
│   │   │   ├── Login.jsx
│   │   │   └── Signup.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── SkillNode.jsx              # skill card: locked / unlockable / unlocked states
│   │   │   └── SkillModal.jsx             # modal: skill info + filming instructions + upload button
│   │   ├── App.jsx                    # routes: /, /skill-tree, /track/:trackId, /login, /signup
│   │   └── supabaseClient.js          # single shared Supabase client
├── backend/
│   ├── main.py                        # FastAPI app, /upload endpoint
│   ├── database.py                    # single shared Supabase client
│   ├── services/
│   │   ├── pose_service.py            # MediaPipe landmark extraction
│   │   └── analysis/
│   │       ├── __init__.py            # exports analyse_pull_up, analyse_push_up
│   │       ├── _shared.py             # calculate_angle, smoothing, body alignment
│   │       ├── pull_up.py
│   │       └── push_up.py
│   └── models/
│       └── pose_models.py             # Pydantic models
└── CLAUDE.md
```

## Skill tree navigation

- `/skill-tree` — interactive SVG muscle map; hovering muscles highlights the track colour; clicking navigates to that track
- `/track/push` → `/track/pull` → `/track/legs` → `/track/core` — one page per track, renders skills from Supabase
- Track colours: push=#f59e0b (amber), pull=#60a5fa (blue), core=#a78bfa (purple), legs=#34d399 (green)

## User flow

1. User lands on the skill tree — four tracks (push, pull, legs, core), each a vertical chain of skill nodes
2. Locked skills show a demo video; skills with unmet prerequisites are greyed out
3. User clicks an unlockable skill → modal opens with skill info and an upload button
4. User uploads a video → backend runs MediaPipe + form analysis against that skill's specific criteria
5. Pass → skill marked unlocked, user's video saved to Supabase Storage, node now shows their video
6. Fail → Claude API feedback shown, user can try again

## MVP features

1. **Skill tree UI** — RPG-style visual map with four tracks: push, pull, legs, core
2. **User accounts** — Supabase auth; all progress and videos tied to a user
3. **Video upload + pose extraction + form feedback** — user uploads a video for a specific skill; before uploading, the skill node shows filming instructions (e.g. "film from the side, full body in frame") to ensure accurate landmark detection. Backend runs MediaPipe and returns structured feedback cards (one per form check, each pass or fail). While the video is processing, the frontend displays the uploaded video with the MediaPipe skeleton overlay rendered on top.
4. **Pass/fail unlock verdict** — a skill is unlocked if and only if every form check card returns pass. The set of checks that run is determined by which skill is being attempted (e.g. pull-up checks for a pull-up skill). Claude API provides narrative feedback text alongside the cards.
5. **Video storage** — unlock video saved to Supabase Storage, replaces demo video on the node

## Database schema

**`skills`** — master list of all skills (not per-user)
- `id`, `name`, `track` (push/pull/legs/core), `description`
- `demo_video_url` (nullable — may not have filmed yet)
- `analysis_key` (nullable — e.g. `"push_up"`; null means no automated analysis yet)
- `pass_threshold` (float, 0–1)
- `order_in_track` (integer, controls visual position)
- `filming_instructions` (text — shown to user before upload, e.g. "Film from the side. Ensure your full body is visible from head to toe. Keep the camera steady.")

**`skill_prerequisites`** — junction table, many-to-many
- `skill_id` → skills, `requires_skill_id` → skills
- No track restriction — cross-track prerequisites are allowed (e.g. muscle-up requires pull-up + dip)

**`user_skills`** — user progress per skill
- `user_id` → auth.users, `skill_id` → skills
- `status`: `"unlockable"` or `"unlocked"` (no row = locked, computed from prerequisites)
- `unlock_video_url` (nullable), `unlocked_at` (nullable), `attempt_count`
- Rows only created on first interaction — not pre-seeded at signup

**`skill_attempts`** — one row per upload attempt, preserved permanently as history
- `id`, `user_id` → auth.users, `skill_id` → skills
- `passed` (boolean)
- `feedback` (JSONB — the full checks array, e.g. `[{"check": "bottom_extension", "passed": true, "message": "..."}]`)
- `video_url` (nullable — only stored for passing attempts to save storage)
- `attempted_at` (timestamp)
- On pass: write attempt row, then update `user_skills` to `"unlocked"` and copy `video_url` there

## Out of scope for MVP

- Real-time webcam analysis
- Mobile app
- Social features

## Coding guidelines

**General:**
- I am learning several of these technologies for the first time, so always explain your reasoning and non-obvious decisions as comments or alongside the code
- Write clean, readable code over clever code — I need to be able to explain every line in an interview
- Keep functions small and single-purpose
- Use meaningful variable names — no single letter variables outside of loop counters

**When I ask for help:**
- If I have not attempted the problem yet, encourage me to try first before giving me the full solution
- Explain concepts before showing implementation where possible
- If I ask you to implement something large, break it into small steps and check I understand each one before moving on
- Flag any dependencies I need to install

**Frontend (React):**
- Functional components only, use hooks
- Keep components small and focused
- Use React Router for navigation

**Backend (FastAPI):**
- Separate routes, services, and models clearly
- Add docstrings to all functions
- Return clear error messages with appropriate HTTP status codes

**Python:**
- Type hints on all functions
- Follow PEP 8
- Add comments explaining MediaPipe landmark indices and angle calculation logic — these are not obvious

## Key domain knowledge (calisthenics)

Filming requirements per exercise (shown to user before upload):
- **Pull-up**: film from the side, full body in frame (head to feet), bar at the top of frame. Side-on is required so elbow angle and body alignment are visible. Front-facing occludes the near/far arm and makes angle calculation unreliable.
- **Push-up**: film from the side, full body in frame. Side-on is required so elbow angle and body alignment are visible. Front-facing occludes the near/far arm and makes angle calculation unreliable.
- **Core skills**: film from the side, full body in frame. Bar at the top of frame if using a bar; enough floor visible to confirm hip height if using parallettes or floor.
- **Legs skills** (e.g. squat progressions): film from the side, full body in frame, feet flat on ground visible.

Form checkpoints for pull-up:
- Bottom position: arms fully extended, slight hollow body
- Top position: chin clearly above the bar, elbows pulled down and back
- Throughout: no kipping, body stays straight, elbows should not flare excessively

Form checkpoints for push-up:
- Bottom position: chest close to the ground, elbows at roughly 45 degrees from body
- Top position: arms fully extended, body in a straight plank line
- Throughout: no hip sag, no flared elbows, head neutral

MediaPipe landmark indices relevant to these exercises:
- 11: left shoulder, 12: right shoulder
- 13: left elbow, 14: right elbow
- 15: left wrist, 16: right wrist
- 23: left hip, 24: right hip
- 25: left knee, 26: right knee

