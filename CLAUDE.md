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
- Push track form analysis: Push-up, Bent Arm Planche, Archer Push-up, Straddle Planche, One-arm Push-up, Handstand, Handstand Push-up, 90° Handstand Push-up (full push track complete)
  - Rep-based (archer push-up): per-side elbow tracking, min() trick for working arm, checks at bottom frame (chest near floor)
  - Static hold (bent arm planche): body horizontal + arms bent (<110°) + 3s streak; returns hold_seconds
  - Wholesale call (straddle planche): calls analyse_straddle_front_lever + renames exercise key — geometry identical from side camera
  - Wholesale reuse (one-arm push-up): uses wrist-shoulder vertical distance for rep detection (elbow angle unreliable from side-on view for vertical arm); exercise name only differs from push_up.py otherwise
  - Inverted exercises (handstand, handstand_push_up, handstand_push_up_90): pose_service.py flips the video vertically before MediaPipe (cv2.flip(frame, 0)); model sees upright human → standard coordinate space; main.py dispatches via INVERTED_EXERCISES set
  - Handstand: static hold streak — body_alignment + arm_lockout + 3s simultaneous; per-frame body angle computed inline (shoulder-hip-knee); returns hold_seconds
  - Handstand Push-up: pull-up style rep detection on flipped landmarks (local MAX = extended = lockout, local MIN = flexed = head near floor); reuses _check_bottom_extension + _check_top_flexion + _check_body_alignment
  - 90° Handstand Push-up: same as HSPu + _check_upper_arm_horizontal (abs(shoulder_y − elbow_y) < 0.05 at flexed frame; absolute y-difference is preserved under vertical flip)
- Legs track form analysis: Squat, Bulgarian Split Squat, Pistol Squat (all with rep detection + form checks)
  - Bulgarian split squat + pistol squat use dual-signal rep detection: min(L,R) for bottom, max(L,R) for top — avoids the rear/free leg dragging the signal below the top threshold
  - Pistol squat free leg check skips frames where working knee < 100° (occlusion zone — free knee hides behind working leg at depth)
  - pose_service.py LANDMARK_NAMES includes ankles (indices 27/28) — required by all legs and core analysers
- Core track form analysis: Leg Raise, Toes to Bar, L-sit, One-arm Toes to Bar (L-sit is a static hold — pass = ≥3s consecutive hold where all criteria are simultaneously met; 3 diagnostic cards + 1 hold_duration card)
- Side-on camera accuracy fixes across pull and core tracks:
  - `_compute_elbow_angles`, `_compute_hip_angles`, `_compute_knee_angles` in `_shared.py` now use visibility-aware averaging: use only the side(s) where all three joints have visibility ≥ 0.5; fallback to raw average only when neither side clears the threshold. Previously both sides were blindly averaged — the far (occluded) arm/leg's MediaPipe estimate contaminated the signal with confident-but-wrong coordinates.
  - `_check_kipping` (pull_up.py): tracks hip y (not shoulder y — hips oscillate in a kip, not shoulders), applies 3-frame smoothing before computing deltas, uses 95th-percentile delta (not max — max fires on a single outlier frame); threshold 0.05. `_check_no_swing` (leg_raise.py, imported by toes_to_bar.py and one_arm_toes_to_bar.py) applies the same p95 pattern.
  - `muscle_up.py` above-bar lockout: hip and wrist y-values now use only visible side(s)
  - `toes_to_bar.py` height check: ankle and wrist y-values at top frames now use visibility-aware averaging
- Analysis calibration during demo recording (Step 14):
  - `_detect_pullup_rep_phases` (pull_up.py): `window` parametrized (default 11); `explosive_pull_up.py` passes `window=5` for short single-rep videos where window=11 flattens the signal
  - `_check_bottom_extension` (pull_up.py): `threshold` parametrized (default 160)
  - `explosive_pull_up.py`: chest-to-bar tolerance `avg_gap >= -0.05` (wrist landmark sits slightly above bar level)
  - `muscle_up.py`: above-bar lockout uses temporal sequence — scan frames after deepest pull (min elbow angle) for any frame with elbow > 150°; avoids wrist landmark position assumptions. `rep_count` now returned in result dict.
  - `lsit.py`: average hip angle `< 120°` (ankle droop inflates reading), average elbow `> 140°` (forward lean for counterbalance); per-frame streak condition `h<130 and k>150 and e>130` — raw frames noisier than per-check averages so streak gate is looser than average thresholds
  - `_check_leg_straightness`, `_check_body_alignment`, `_check_bottom_extension` in `_shared.py`: all parametrized with a `threshold` argument; existing call sites use the default, callers needing different behaviour pass explicit values
  - `toes_to_bar.py` + `one_arm_toes_to_bar.py`: `_check_leg_straightness(threshold=125)` — hamstrings maximally stretched at full toes-to-bar, some natural knee bend unavoidable
  - `one_arm_pull_up.py`: `_check_bottom_extension(threshold=155)` + `_check_body_alignment(threshold=145)` — single arm reads slightly compressed; body rotation toward gripping arm reads as hip sag from side camera
- Frontend unlock animation fixes:
  - `SkillModal.jsx`: `handleClose` wrapper calls `handleShowcaseChoice(false)` (implicit skip) before `onClose()` when `pendingAttempt` exists — closing without choosing now unlocks the skill instead of leaving it in limbo
  - `TrackPage.jsx`: `pendingUnlockRef.current` set before the first `await` in the skip path — fixes race condition where `onClose` read the ref synchronously before the async callback had a chance to set it
- Rep counting with smoothed signal (window=11) + de-duplicated phase events to prevent overcounting
- All dynamic analysers evaluate form on the first detected rep only — prevents multi-rep averaging from failing a user who had a clean first rep
- Filming instructions updated in Supabase: dynamic skills say "film one clean rep, trim to just that rep"; L-sit says "trim to just your hold"
- SkillModal displays hold duration ("Xs held") instead of rep count for static holds
- Supabase: schema (4 tables), RLS policies, storage buckets (demo-videos, unlock-videos)
- Auth: login, signup, session persistence via AuthContext
- Muscle map landing page (interactive SVG at /skill-tree, now labelled "Skill Trees")
- Track pages at /track/:trackId — column-based skill tree with real Supabase data, locked/unlockable/unlocked states, H-branch SVG connectors
- SkillNode component (3 visual states, per-skill SVG stick-figure icons, box-shadow glow on unlocked)
- SkillModal (skill info, collapsible general filming tips incl. trim/rep-quality emphasis + demo reference hint, exercise-specific filming instructions, autoplay video previews, upload button)
- Full upload flow: file picker → uploading state with video preview → MediaPipe skeleton overlay on result (knee-to-ankle lines included) → pass/fail verdict → feedback cards
- Supabase writes on attempt: skill_attempts (always), user_skills + Storage upload (on pass)
- Showcase replacement prompt after any passing attempt: first-time unlock shows "Save/Skip", re-attempt shows "Lock it in/Keep current"; storage uses timestamped paths (always INSERT, avoids needing UPDATE RLS permission); old file deleted on replace
- Skill node flips to unlocked immediately after pass (local state + persisted to DB)
- Reopening an unlocked skill shows the user's own unlock video (no label) + "Improve" button to re-attempt
- Sign-in banner for unauthenticated users (upload still works, results not saved)
- RPG UI polish: Bebas Neue titles, Rajdhani body font, dot-grid + vignette background, 3-level connector colours, glowing unlocked paths, track switcher on track pages, navbar background
- Gemini LLM narrative feedback (gracefully degraded — returns null if API unavailable, UI skips the section)
- Deployment prep: hardcoded localhost URLs replaced with env vars, CORS origin configurable via `FRONTEND_URL`, `vercel.json` SPA rewrite rule added

**Next:**
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
│   │   │   └── SkillModal.jsx             # modal: skill info + collapsible general filming tips + exercise-specific filming instructions + upload button
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

