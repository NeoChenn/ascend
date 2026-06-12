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

Once unlocked, a skill stores the user's own video and they can rewatch it in the skill modal at any time.

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
| Backend deployment | Railway |
| LLM feedback | Gemini API (google-genai) |

## Current build status

**Done:**
- Video upload + MediaPipe pose extraction
- Pull track form analysis: Pull-up, Explosive Pull-up, Muscle-up, Archer Pull-up, Straddle Front Lever, One-arm Pull-up (full pull track complete)
  - Rep-based (pull-up, explosive pull-up, archer pull-up): elbow angle rep detection, first-rep-only evaluation
  - Scan-based (muscle-up): no rep detection — scan all frames for pull_depth (min elbow < 70°) and above_bar_lockout
  - Static hold (straddle front lever): ≥3s consecutive streak where body horizontal + arms locked simultaneously; returns hold_seconds
  - Wholesale reuse (one-arm pull-up): identical to pull_up.py, exercise name only differs
  - Archer pull-up uses per-side elbow angles (not averaged) to identify working vs assisting arm
- Push track form analysis: Push-up, Bent Arm Planche, Archer Push-up, Straddle Planche, One-arm Push-up (partial — Handstand/HSPu/90° HSPu deferred, require inverted detection)
  - Rep-based (archer push-up): per-side elbow tracking, min() trick for working arm, checks at bottom frame (chest near floor)
  - Static hold (bent arm planche): body horizontal + arms bent (<110°) + 3s streak; returns hold_seconds
  - Wholesale call (straddle planche): calls analyse_straddle_front_lever + renames exercise key — geometry identical from side camera
  - Wholesale reuse (one-arm push-up): identical to push_up.py, exercise name only differs
- Legs track form analysis: Squat, Bulgarian Split Squat, Pistol Squat (all with rep detection + form checks)
- Core track form analysis: Leg Raise, Toes to Bar, L-sit, One-arm Toes to Bar (L-sit is a static hold — pass = ≥3s consecutive hold where all criteria are simultaneously met; 3 diagnostic cards + 1 hold_duration card)
- Rep counting with smoothed signal (window=11) + de-duplicated phase events to prevent overcounting
- All dynamic analysers evaluate form on the first detected rep only — prevents multi-rep averaging from failing a user who had a clean first rep
- Filming instructions updated in Supabase: dynamic skills say "film one clean rep, trim to just that rep"; L-sit says "trim to just your hold"
- SkillModal displays hold duration ("Xs held") instead of rep count for static holds
- Supabase: schema (4 tables), RLS policies, storage buckets (demo-videos, unlock-videos)
- Auth: login, signup, session persistence via AuthContext
- Muscle map landing page (interactive SVG at /skill-tree, now labelled "Skill Trees")
- Track pages at /track/:trackId — column-based skill tree with real Supabase data, locked/unlockable/unlocked states, H-branch SVG connectors
- SkillNode component (3 visual states, per-skill SVG stick-figure icons, box-shadow glow on unlocked)
- SkillModal (skill info, filming instructions, autoplay video previews, upload button)
- Full upload flow: file picker → uploading state with video preview → MediaPipe skeleton overlay on result → pass/fail verdict → feedback cards
- Supabase writes on attempt: skill_attempts (always), user_skills + Storage upload (on pass)
- Skill node flips to unlocked immediately after pass (local state + persisted to DB)
- Reopening an unlocked skill shows the user's own unlock video + option to re-attempt
- Sign-in banner for unauthenticated users (upload still works, results not saved)
- RPG UI polish: Bebas Neue titles, Rajdhani body font, dot-grid + vignette background, 3-level connector colours, glowing unlocked paths, track switcher on track pages, navbar background
- Gemini LLM narrative feedback (gracefully degraded — returns null if API unavailable, UI skips the section)
- Deployment prep: hardcoded localhost URLs replaced with env vars, CORS origin configurable via `FRONTEND_URL`, `vercel.json` SPA rewrite rule added

**Next:**
- Remaining push/pull track exercises (Explosive Pull-up, Muscle-up, Archer Push-up, etc.)
- Film and upload demo videos for skill nodes

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
│   │   │   ├── Login.jsx
│   │   │   └── Signup.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── SkillNode.jsx              # skill card: locked / unlockable / unlocked states
│   │   │   ├── SkillIcons.jsx             # 21 SVG stick-figure icons (one per skill), all using currentColor
│   │   │   └── SkillModal.jsx             # modal: skill info + filming instructions + upload button
│   │   ├── App.jsx                    # routes: /, /skill-tree, /track/:trackId, /login, /signup
│   │   └── supabaseClient.js          # single shared Supabase client
├── backend/
│   ├── main.py                        # FastAPI app, /upload endpoint, ANALYSERS dispatch dict
│   ├── database.py                    # single shared Supabase client
│   ├── services/
│   │   ├── pose_service.py            # MediaPipe landmark extraction
│   │   └── analysis/
│   │       ├── __init__.py            # exports all analyser functions
│   │       ├── _shared.py             # calculate_angle, smoothing, body/torso alignment, knee angles
│   │       ├── pull_up.py
│   │       ├── push_up.py
│   │       ├── squat.py
│   │       ├── bulgarian_split_squat.py
│   │       ├── pistol_squat.py
│   │       ├── leg_raise.py
│   │       ├── toes_to_bar.py
│   │       ├── lsit.py
│   │       └── one_arm_toes_to_bar.py
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
2. Skills with unmet prerequisites are greyed out (locked); skills whose prerequisites are met are unlockable
3. User clicks an unlockable skill → modal opens with skill info, filming instructions, and an upload button
4. User uploads a video → backend runs MediaPipe + form analysis against that skill's specific criteria
5. Pass → skill flips to unlocked, user's video saved to Supabase Storage; user can rewatch it by clicking the node again
6. Fail → structured feedback cards shown (one per form check, each pass or fail); user can try again

## MVP features

1. **Skill tree UI** — RPG-style visual map with four tracks: push, pull, legs, core
2. **User accounts** — Supabase auth; all progress and videos tied to a user
3. **Video upload + pose extraction + form feedback** — user uploads a video for a specific skill; before uploading, the skill node shows filming instructions (e.g. "film from the side, full body in frame") to ensure accurate landmark detection. Backend runs MediaPipe and returns structured feedback cards (one per form check, each pass or fail). While the video is processing, the frontend displays the uploaded video with the MediaPipe skeleton overlay rendered on top.
4. **Pass/fail unlock verdict** — a skill is unlocked if and only if every form check card returns pass. The set of checks that run is determined by which skill is being attempted (e.g. pull-up checks for a pull-up skill).
5. **Video storage** — unlock video saved to Supabase Storage; user can reopen the skill node at any time to rewatch it

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

## Stretch goals (post-MVP)

- **Claude API narrative feedback** — LLM-generated paragraph summarising the attempt alongside the structured cards
- **Demo videos on skill nodes** — developer-filmed demo video plays on each locked skill; replaced by the user's own video on unlock
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

