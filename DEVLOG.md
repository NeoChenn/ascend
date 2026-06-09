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
- **VIDEO mode over IMAGE mode** — `RunningMode.VIDEO` tracks joints across frames rather than re-detecting from scratch each time, which is faster and more stable. timestamp_ms tells MediaPipe where in time each frame sits so it can reason about movement between frames.So instead of treating each frame independently, it uses temporal context — meaning it considers how the body was positioned in previous frames to make better predictions about the current frame. This is what makes video pose estimation smoother and more stable than running image detection on each frame independently.
- **Computed timestamps over `CAP_PROP_POS_MSEC`** — VIDEO mode requires strictly increasing timestamps. `cap.get(CAP_PROP_POS_MSEC)` can be unreliable for some codecs, so timestamps are computed from frame index and FPS instead.

### What's next
- Angle-based form analysis for pull-ups (shoulder–elbow–wrist angle, body alignment)
- Return structured feedback alongside the landmark data

---


## Step 5 — Form analysis logic (pull-up)
*Date: June 2026*

### What I built
- `backend/services/analysis_service.py` — all pull-up form analysis logic:
  - `calculate_angle()` — given three landmark dicts (A, B, C), returns the angle in degrees at joint B using the vector dot-product formula
  - `_smooth_signal()` — 5-frame moving average using `numpy.convolve` to remove per-frame jitter from the elbow angle signal
  - `detect_rep_phases()` — finds the bottom and top of each rep by tracking elbow angle over time; returns rep pairs as `(bottom_frame_idx, top_frame_idx)`
  - Four form check helpers (`_check_bottom_extension`, `_check_top_flexion`, `_check_body_alignment`, `_check_kipping`) + `analyse_pull_up()` as the main entry point
- Added `FormCheck` and `FormFeedback` Pydantic models to `backend/models/pose_models.py` to define the shape of the feedback JSON
- Updated `/upload` endpoint in `main.py` to call `analyse_pull_up` and include a `feedback` field in the response
- Updated `frontend/src/pages/Upload.jsx` to read `data.feedback` from the response and render a pass/fail card for each check
- Updated `Upload.module.css` with green (pass) and red (fail) feedback card styles

### What I learned

**Joint angle calculation using vectors:**
To measure how bent an elbow is, you need three points: shoulder (A), elbow (B), wrist (C). You build two vectors both starting at B — one pointing toward A, one toward C — then use the dot-product formula:

```
cos(angle) = (BA · BC) / (|BA| * |BC|)
angle = degrees(arccos(cos_angle))
```

The dot product of two vectors tells you how much they point in the same direction. When the elbow is straight (shoulder-elbow-wrist form a line), the vectors point in opposite directions and the angle is 180°. When fully bent, the angle is small (30–60°). You must clamp the input to `arccos` between -1 and 1 using `numpy.clip` because floating-point arithmetic can produce values like `1.0000000002`, which would raise a math domain error.

**Signal smoothing:**
Raw MediaPipe output is noisy — the elbow angle jitters ±5° frame-to-frame even when the person is holding still. Without smoothing, simple local-max finding would report hundreds of fake reps. A 5-frame moving average (done with `numpy.convolve` and a uniform kernel) is enough to remove that noise while preserving the actual rep shape.

**Rep detection from a 1D signal:**
The elbow angle over time is a wave: it starts near 180° (arms straight, bottom of rep), drops to ~60–90° (arms bent, top of rep), then rises again. A rep is one full cycle of that wave. Finding reps means finding local maxima (bottoms, angle > 150°) and local minima (tops, angle < 110°), then pairing each max with the next min that follows it in time. A fallback of `[(0, last_frame)]` handles the case where no clear reps are detected — the form checks still run on whatever data is available.

**MediaPipe y-axis is inverted:**
`y = 0` is the top of the screen, `y = 1` is the bottom. "Moving up" means y *decreases*. This matters for kipping detection: a sudden upward shoulder jerk shows up as a sudden *decrease* in shoulder y between consecutive frames.

### Decisions made

**Form check thresholds — why these specific angles:**
- **Bottom extension > 160°**: Full anatomical extension of the elbow is 180°. Anything above 160° is close enough to count as straight — below that, the athlete is clearly not locking out between reps, which shortens range of motion. As someone who trains calisthenics, I know that not locking out is a common form cheat in high-rep sets.
- **Top flexion < 90°**: This is the chin-over-bar criterion. An elbow angle above 90° at the top almost always means the chin has not cleared the bar. Based on my own training experience, getting the elbow to 90° or below correlates reliably with chin height.
- **Body alignment > 160°**: Measured as the shoulder→hip→knee angle. Perfect body tension gives 180°. A bit of hollow body is normal and acceptable — the 160° threshold flags obvious hip sag without penalising athletes who naturally hold a slight hollow position.
- **Kipping threshold 0.03 (normalised)**: At 720p, the person's body might fill ~60% of frame height, so 0.03 normalised ≈ 13px in one frame. Legitimate pull-up movement between frames is a few pixels. Kipping from a hip swing moves the whole torso upward much faster — field-tested to be above this threshold.

**No scipy dependency:**
`scipy.signal.find_peaks` would have made rep detection cleaner, but it's an extra dependency that's not otherwise used in the project. Writing a simple local-max/min finder with a plain Python loop was only ~10 lines and easy to explain in an interview without needing to reference an external library.

**Average left + right elbow for rep detection:**
The camera might be side-on (only one arm visible) or front-facing (both arms visible). When one arm is occluded, MediaPipe often mirrors its position. Averaging both elbows handles both camera angles gracefully — the average stays reasonable either way.

**Skip low-visibility frames:**
Any landmark with `visibility < 0.5` means MediaPipe isn't confident it can see that joint. Computing an angle on an occluded joint would produce a meaningless number that pollutes the averages. Better to skip those frames entirely.

### What's next
- Test with real pull-up video footage and adjust thresholds if needed
- Push-up form analysis (similar structure but different joints and checks)
- Add a loading state to the frontend while the video is being processed (long videos can take several seconds)

---

## Step 6 — Form analysis (push-up) + feedback UI
*Date: June 2026*

### What I built
- Push-up form analysis in `backend/services/analysis_service.py`:
  - `_detect_pushup_rep_phases()` — rep detection with inverted thresholds vs pull-up (bottom = local min < 100°, top = local max > 150°)
  - `_check_pushup_top_extension()` — elbow angle at top > 160° (arms locked out)
  - `_check_pushup_bottom_depth()` — elbow angle at bottom < 100° (chest near floor)
  - `analyse_push_up()` — entry point; reuses `_check_body_alignment` from pull-up unchanged
- Refactored `detect_rep_phases` into `_detect_pullup_rep_phases` and extracted `_compute_elbow_angles` as a shared helper used by both exercise detectors
- Updated `/upload` endpoint to accept an `exercise` form field and route to the correct analysis function
- Added exercise dropdown (Pull-up / Push-up) to `Upload.jsx`, included in the FormData sent to the backend
- Bug fix: `_check_body_alignment` was silently returning "could not assess" for all push-up videos (see below)

### What broke / what was hard
- **Body alignment check always failing for push-ups** — `_check_body_alignment` originally required all six joints (left AND right shoulder, hip, knee) to have visibility ≥ 0.5 before computing any angle. When filming from the side — which is required for accurate elbow angle measurement — the far-side joints are always occluded and have low MediaPipe visibility. This caused every frame to be skipped, leaving `valid_angles` empty and returning the "could not assess" fallback message even for perfect form. Fixed by checking each side independently: if the left-side joints are all visible, compute the left angle; same for right; average whichever sides are usable. At least one side will always be visible in a side-on video.

### What I learned

**Push-up rep detection is the inverse of pull-up:**
The elbow angle signal has the same shape — a wave oscillating between a minimum and maximum — but the semantics are flipped. In a pull-up, the bottom (rest position) is arms straight = local maximum (~180°), and the top (peak effort) is arms bent = local minimum (~60°). In a push-up, the bottom (lowest point) is arms bent = local minimum (~70–90°), and the top (starting/ending position) is arms extended = local maximum (~160–180°). The rep detection algorithm is identical in structure; only the thresholds and which extreme counts as "bottom" vs "top" change.

**MediaPipe visibility is joint-specific, not frame-specific:**
I had assumed that if MediaPipe detected a pose in a frame, all landmarks in that frame would be usable. That's wrong — MediaPipe can confidently detect a pose while simultaneously reporting low visibility on specific joints that are occluded or outside the frame. A side-on camera will reliably occlude the far-side shoulder, hip, and knee, giving those landmarks visibility scores well below 0.5 even when the overall pose detection is confident. The right response is to filter at the individual joint level, not the frame level.

**`Form(...)` for mixed file + text fields in FastAPI:**
When a POST request needs both a file upload and a text field (like `exercise`), FastAPI handles them both as multipart form data. On the backend, text fields use `Form(...)` instead of `Body(...)`. On the frontend, they're both appended to the same `FormData` object — the browser handles the multipart encoding automatically.

### Decisions made

**Push-up threshold rationale:**
- **Top extension > 160°**: Same threshold as pull-up bottom extension. Full lockout is important — stopping short at the top means the triceps never complete their range of motion, and the athlete doesn't build pressing strength through the full movement.
- **Bottom depth < 100°**: At genuine full depth (chest touching or nearly touching the ground), the elbow is around 70–90° depending on torso length and hand position. 100° gives a small buffer while clearly flagging partial reps where the athlete is stopping well above the floor.
- **Body alignment > 160°**: Reused from pull-up — the shoulder→hip→knee angle catches both hip sag (hips dropping below the plank line) and pike (hips rising above it). Push-up alignment failure is usually one of these two, so the same check works for both exercises.

**Elbow flare skipped for MVP:**
CLAUDE.md notes that elbows should be at roughly 45° from the body. Detecting this reliably requires seeing the front of the body — you'd compare horizontal elbow spread to shoulder width. From a side-on camera (which is required for everything else), this is completely invisible. Not worth implementing until the app can confirm camera orientation.

**architecture note — not splitting `analysis_service.py` yet:**
With two exercises the file is manageable. The right time to split is when adding a third exercise — at that point, the natural structure would be `services/analysis/_shared.py` (shared utilities), `services/analysis/pull_up.py`, `services/analysis/push_up.py`, etc. Doing it now for two exercises would be premature.

### What's next
- Supabase setup + user authentication
- Save upload history and skill progress to the database
- Loading state on the frontend during video processing

---

## Design pivot — skill-tree-first
*Date: June 2026*

### Decision

Reframed the app from a generic "upload a video, get feedback" tool to a skill-tree-first RPG-style progression app. The skill tree is now the emotional core — form analysis exists to serve it, not the other way around.

### New user flow
1. User lands on the skill tree (four tracks: push, pull, legs, core)
2. Each node shows a demo video until unlocked
3. User picks an unlockable skill → uploads a video attempting it
4. While the video processes, the frontend shows the uploaded video with the MediaPipe skeleton overlay rendered on top
5. Backend runs the exercise's form check functions and returns structured feedback cards (one per check, pass or fail)
6. **Skill unlocks if and only if every card is a pass** — no partial credit, no score threshold
7. On unlock: video saved to Supabase Storage, node now shows the user's own video permanently

### Why this is better
- The form analysis now has a purpose — it's the gate to unlock a skill, not just a diagnostic tool
- The RPG framing makes progression visible and emotionally rewarding
- Demo-video-replaced-by-your-video is a strong memorable feature for a CV project

### What this changes architecturally
- Supabase is now required earlier (user accounts needed before skill progress can be saved)
- Skills need a database table with `analysis_key` (which analysis function to run), `demo_video_url`, and prerequisite relationships
- The `/upload` endpoint needs to know which skill is being attempted, not just which exercise
- Pass/fail is binary: all form check functions must return `passed: True`
- Claude API moved from stretch goal to planned feature — provides narrative feedback text alongside the cards

### Database schema decided
See CLAUDE.md for full schema. Key tables: `skills`, `skill_prerequisites` (junction), `user_skills` (progress per user). User skill rows are only created on first interaction — not pre-seeded at signup. Locked/unlockable status is computed from prerequisites at query time.

---

## Step 7 — Supabase setup + user auth
*Date: June 2026*

### What I built

**Supabase project:**
- Created Supabase project and designed the full database schema (4 tables): `skills`, `skill_prerequisites`, `user_skills`, `skill_attempts`
- Set up Row Level Security (RLS) policies: `skills` and `skill_prerequisites` are publicly readable; `user_skills` and `skill_attempts` are user-owned (users can only read/write their own rows)
- Created two Storage buckets: `demo-videos` (public — anyone can view demo clips on the skill tree) and `unlock-videos` (private — signed URLs required, users can only access their own folder)
- Installed `supabase` and `python-dotenv` on the backend; `@supabase/supabase-js` on the frontend
- Created `backend/database.py` and `frontend/src/supabaseClient.js` — single shared client instances imported wherever needed

**Auth:**
- `frontend/src/context/AuthContext.jsx` — React context that holds the current user session. Uses `supabase.auth.getSession()` on mount to restore any existing session, then `onAuthStateChange` to stay in sync with future login/logout/token refresh events. Exposes `user` and `signOut` to any component via `useAuth()` hook.
- `frontend/src/pages/Login.jsx` — email + password form calling `supabase.auth.signInWithPassword`. Redirects to /skill-tree on success, displays error message on failure.
- `frontend/src/pages/Signup.jsx` — same structure, calls `supabase.auth.signUp`
- Updated `Navbar.jsx` — shows user email + Sign out button when logged in; Sign in / Sign up links when not
- Updated `App.jsx` — wrapped in `<AuthProvider>`, added `/login` and `/signup` routes
- Updated `Home.jsx` — rebranded to Ascend with skill-tree-first copy

### What broke / what was hard

**Email confirmations blocking signup** — Supabase enables email confirmation by default. On signup, the account is created but no session is started until the user clicks the confirmation link. This meant `supabase.auth.signUp` appeared to succeed (no error returned) but `user` was still null and the redirect to /skill-tree left the user looking logged out. Fixed by disabling email confirmations in Supabase → Authentication → Settings for local dev.

**Loading flash before session resolves** — On page refresh, `AuthContext` initialises with `user = null` before `getSession()` completes. Without a `loading` guard, the app briefly renders as "logged out" even for authenticated users (navbar flashes the login links before switching to the email). Fixed by keeping `loading: true` until the first session check resolves and not rendering children until then.

### What I learned

**What Row Level Security is:**
RLS is PostgreSQL's built-in access control system. Every query to a Supabase table runs through the policies you define. Without any policy, a table with RLS enabled rejects all requests. `USING (auth.uid() = user_id)` is the standard pattern for user-owned rows — Supabase injects the authenticated user's ID from their JWT into `auth.uid()`, so the database itself enforces that users can only touch their own data, even if the frontend sends a malicious request.

**Core database concepts applied for the first time:**
- **Foreign keys** — a column in one table that references the primary key of another, enforcing that the value must exist in the referenced table. `skill_id UUID REFERENCES skills(id)` means you cannot insert a `skill_attempts` row with a `skill_id` that doesn't correspond to a real skill — the database rejects it automatically. This is called referential integrity.
- **`ON DELETE CASCADE`** — when a parent row is deleted, all child rows referencing it are automatically deleted too. Both `user_skills` and `skill_attempts` cascade from `auth.users`, so deleting a user account cleans up all their data automatically.
- **Composite primary key** — `skill_prerequisites` uses `PRIMARY KEY (skill_id, requires_skill_id)` instead of a separate UUID. Neither column alone is unique, but the pair always is — "skill X requires skill Y" should only ever appear once.
- **`UNIQUE (user_id, skill_id)`** on `user_skills` — prevents the backend from accidentally inserting two progress rows for the same user and skill, regardless of what the application code does. The database enforces it as a last line of defence.


**Why `onAuthStateChange` instead of just `getSession`:**
`getSession()` is a one-time check. If you only call it on mount, the UI won't update when the user signs in or out in another tab, or when the JWT silently refreshes in the background. `onAuthStateChange` is a persistent subscription that fires on every auth event for the lifetime of the component — it's the correct way to keep auth state in sync in a React app.I

**What a React context is:**
A context is a way to share state across the component tree without passing props down through every level ("prop drilling"). `AuthContext` lives at the top of the tree in `App.jsx`, and any component anywhere in the tree can call `useAuth()` to get the current user — the Navbar, the skill tree nodes, the upload modal. Without context, you'd have to pass `user` as a prop through every intermediate component.

**React `useEffect` and the component lifecycle:**
- **Rendering** — React recalculating what the UI should look like and updating the DOM. Happens many times throughout a component's life — whenever state or props change. The component still exists, it's just being updated.
- **Mounting** — the component is added to the page for the first time. `useEffect` with `[]` runs once after mount — the correct place for one-time setup like session checks and subscriptions.
- **Unmounting** — the component is removed from the DOM entirely. The cleanup function returned from `useEffect` runs here — the correct place to cancel subscriptions, clear timers, or clean up anything that lives outside React.
- **Why code belongs in `useEffect` rather than the component body** — the component body runs on every render, synchronously, before the DOM updates. Side effects like API calls and subscriptions should run after the DOM is updated and only when needed. `useEffect` with `[]` guarantees this — once on mount, never again on re-render.
- **`useEffect` without `[]`** — runs after every render, after the DOM updates. Not the same as the component body despite similar frequency — the timing difference (after vs during render) matters for side effects.

**How `onAuthStateChange` persists:**
- Supabase maintains its own internal list of registered callbacks entirely outside of React. When you call `onAuthStateChange`, Supabase stores your callback in its own memory. Auth events — login, logout, token refresh — trigger the callback independently of React's render cycle.
- The `subscription` object returned by `onAuthStateChange` is a reference to that registration. It has one method: `unsubscribe()`, which tells Supabase to remove the callback from its internal list.
- Without calling `unsubscribe()` on unmount, Supabase would keep calling the callback forever — even after the component is gone — causing a memory leak. This is why the cleanup function is necessary.
- If you put supabase.auth.onAuthStateChange(...) directly in the component body, you'd create a new subscription on every render — leaking subscriptions until your app runs out of memory.

**JWT forwarding vs service role key:**
When the backend (FastAPI) needs to call Supabase on behalf of a user — e.g. saving their unlock video — there are two options: use the service role key (bypasses all RLS, can read/write anything) or forward the user's JWT from the frontend request and initialise a Supabase client with it (RLS applies, client is scoped to that user). The second approach is correct: it means the database's own access policies enforce security, rather than trusting that the backend won't do anything wrong.

### Decisions made

**"Try before you commit" auth model — no protected routes:**
Initially considered protecting `/skill-tree` and `/upload` to force login. Rejected this because the core value of the app — the skill tree itself — should be visible to everyone. Instead, auth state changes what *actions* are available: guests can browse and run form analysis, but unlocking a skill requires an account. When a guest passes, they see "You passed! Sign in to save your unlock." This is the Duolingo pattern — let users see the value before asking for commitment.

**`skill_attempts` table added for history:**
Originally not in scope. Added because the marginal effort (10 minutes of schema design) is tiny compared to the interview value: "I store every attempt so users can see specific measurements improving between tries." Each attempt stores the full feedback JSON so you can compare check-by-check across attempts. Failed attempt videos are not stored to save storage.

**`user_skills` rows created on interaction, not pre-seeded at signup:**
Considered inserting a row for every skill when a user signs up. Rejected because it creates a maintenance problem: adding new skills later would require a migration to backfill rows for existing users. Instead, a missing row means "not yet interacted" — locked or unlockable status is computed from prerequisites at query time.

**`demo_video_url` nullable on `skills`:**
The developer (me) may not have filmed the demo for every skill before launch. Nullable means the skill can exist in the database and appear in the tree without a demo video yet.

### What's next
- Seed the `skills` table with the initial skill set across all four tracks
- Build the skill tree UI — nodes, tracks, locked/unlockable/unlocked states, prerequisite edges

---

## Step 8 — Skill tree UI, upload flow, and skeleton overlay
*Date: June 2026*

### What I built

**Skill tree UI (data layer):**
- Designed and seeded the full 20-skill tree across 4 tracks in Supabase (push, pull, core, legs), including prerequisite relationships in `skill_prerequisites`
- `SkillNode` component — card with 3 visual states: locked (muted, padlock icon), unlockable (track-colour border + glow, clickable), unlocked (track-colour fill, checkmark). Shows "Requires: X" on locked cards.
- `SkillModal` component — opens when clicking a skill node; shows name, description, filming instructions from Supabase, and an upload button
- `TrackPage` — fetches skills, prerequisites, and the user's unlocked skills from Supabase; computes locked/unlockable/unlocked state for each skill; renders a column-based prerequisite tree with H-shaped SVG connectors

**Upload flow (end-to-end):**
- Wired SkillModal's "Upload attempt" button to the backend `/upload` endpoint with a 4-state machine: `idle → uploading → result → error`
- `uploading` state: shows the selected video immediately via `URL.createObjectURL` (a local blob URL — no upload needed to play it), plus a pulsing "Analysing…" message while the backend processes
- `result` state: shows the video with the MediaPipe skeleton overlay rendered on top via a `<canvas>` element absolutely positioned over the `<video>` element; shows pass/fail verdict banner, rep count, and a feedback card per check; "Try again" button appears only on fail
- Pass/fail verdict computed on the frontend using `skill.pass_threshold` from Supabase (a float 0–1) — this makes the pass threshold configurable per skill without code changes
- Sign-in banner for guests: amber-tinted notice above the upload button when no user is logged in ("Sign in to save your progress"). Upload still works — guests see feedback but nothing is persisted.

**Skeleton overlay:**
- `drawSkeleton()` function draws joint dots (white, cyan border) and connecting lines (cyan) onto a `<canvas>` using the `landmarks_per_frame` array returned by the backend
- A `requestAnimationFrame` draw loop runs continuously once the result is available; each frame maps the video's current time → landmark frame index proportionally across the video's duration
- Canvas intrinsic size is kept in sync with the video's rendered size via `getBoundingClientRect()` — without this the canvas would use its default 300×150 and the skeleton would be drawn at the wrong scale
- `pointer-events: none` on the canvas so video controls under it remain clickable

**Supabase writes (frontend-owned):**
- `TrackPage.handleAttemptComplete` writes to Supabase after every attempt:
  - On pass: uploads the video file to `unlock-videos` storage bucket (path `{userId}/{skillId}.mp4`, overwritten on re-attempt), retrieves the public URL, inserts a `skill_attempts` row (`passed: true`, full feedback JSON, `video_url`), upserts `user_skills` (`status: "unlocked"`, `unlock_video_url`, `unlocked_at`), then updates local React state so the node flips to unlocked instantly without a page reload
  - On fail: inserts a `skill_attempts` row (`passed: false`, feedback JSON, no video URL)
- `user_skills` query extended to also fetch `unlock_video_url` and store it in a map — passed to SkillModal so reopening an unlocked skill shows the user's own video at the top of the modal

**Unlocked skill modal:**
- Both unlockable and unlocked nodes are now clickable (previously unlocked nodes had no `onClick`)
- When reopening an unlocked skill, the modal shows the user's own unlock video in a "Your unlock attempt" section, with filming instructions and the upload button still available below for re-attempts

**Rep counting fix:**
- Increased smoothing window in both `pull_up.py` and `push_up.py` from 5 to 11 frames — at 30 fps, window=5 only covers ~0.17s, not enough to remove inter-frame landmark jitter
- Added de-duplication of consecutive same-type phase events: merge all bottom/top events into a single time-sorted sequence, then if two bottoms appear in a row (or two tops), keep only the later one. This prevents noise at the turning points from generating phantom reps.

### What broke / what was hard

**"permission denied for table skills" (Supabase code 42501):**
The `skills` and `skill_prerequisites` tables showed "API DISABLED" in the Supabase dashboard. Not an RLS issue — it was a Data API exposure setting. Fixed via: Project Settings → API → Data API → confirm `public` schema is listed in Exposed schemas.

**Connector lines pointing at the wrong node:**
First attempt used a tier-based layout (grouping skills by depth). This drew a single H-connector spanning a whole row, so Straddle Planche, Handstand Push-up, and One-arm Push-up all shared one connector even though their prerequisites are in different columns. Fixed by switching to a column-based layout.

**Duplicate nodes in the tree (Explosive Pull-up × 3):**
The initial column-building algorithm traced from each leaf back to the root. When a skill has multiple children, it appeared once per leaf path. Fixed by walking forward from the root to the branch node first, then building chains only from that node's direct children upward — shared ancestors appear exactly once.

**MIME type typo in unlock-videos bucket:**
Storage uploads were rejected with error `"mime type video/mp4 is not supported"`. The root cause was a typo in the bucket's `allowed_mime_types` array: `"ideo/mp4"` (missing the `v`). Fixed via Supabase SQL editor: `UPDATE storage.buckets SET allowed_mime_types = ARRAY['video/mp4', 'video/quicktime', 'video/webm'] WHERE name = 'unlock-videos'`.

**Unlock video not playing — 403 error in DevTools:**
After a pass, the skill's video was empty and DevTools showed a 403 on the video URL. The `unlock-videos` bucket was private, and `supabase.storage.getPublicUrl()` generates a URL without any auth token. A browser `<video>` element fetches the URL with no Supabase auth headers, so Supabase Storage's RLS rejected it. Fixed by making the bucket public: `UPDATE storage.buckets SET public = true WHERE name = 'unlock-videos'`.

**Rep counter returning 3 for a single rep:**
MediaPipe landmark positions jitter ±5° frame-to-frame even on a stationary position. With window=5 smoothing, this noise survived into the local extrema search and created multiple fake phase transitions per rep. Widening the window to 11 and de-duplicating consecutive same-type events reduced false reps to zero for a single-rep test.

### What I learned

**Graph traversal for UI layout:**
The skill prerequisite structure is a DAG (directed acyclic graph). Rendering it correctly as a visual tree required: (1) finding the root (skill with no in-track prerequisites), (2) walking single-child links upward to find the "branch node" — the first skill with more than one child, (3) building one independent column per branch-node child, tracing each up to its leaf. The key insight is that building chains from the root downward (not from leaves upward) prevents shared ancestors from being duplicated.

**SVG for dynamic connector lines:**
Used inline SVG to draw the H-shaped connectors. The SVG width is computed as `columnCount × 200 + (columnCount - 1) × 16` — these constants must match the CSS column width and gap exactly, otherwise the lines don't align with the nodes.

**CSS flex alignment gotcha:**
A 2px-wide connector `<div>` left-aligns if it's nested inside a wrapper `<div>`, even if the parent column has `align-items: center`. Fix: use `flatMap` to make connector divs direct flex children of the column container rather than wrapping each node+connector in a div. With direct children, `align-items: center` actually centres the line on the node.

**`URL.createObjectURL` for instant video preview:**
When the user selects a file, the browser already has the file data in memory. `URL.createObjectURL(file)` creates a temporary `blob:` URL pointing to that in-memory data — the `<video>` element can play it immediately, with no upload required. The URL must be revoked with `URL.revokeObjectURL` when no longer needed to release the memory reference.

**`requestAnimationFrame` for canvas overlay:**
To keep the skeleton overlay in sync with the video as it plays or is scrubbed, a draw loop runs continuously using `requestAnimationFrame`. Each tick: read `video.currentTime`, map it to a landmark frame index proportionally, call `drawSkeleton`. The canvas intrinsic dimensions must be kept in sync with the video's rendered pixel size — `getBoundingClientRect()` gives the rendered size, which changes with viewport resizing. The loop is started/stopped via `useEffect` cleanup to avoid memory leaks.

**Supabase Storage: public vs private buckets:**
A private bucket requires the request to include an auth token (as a query param or header). A browser `<video src="...">` element sends a plain HTTP request with no Supabase auth headers, so private bucket URLs always 403. The right pattern is: public bucket (URL is cacheable by CDN, no auth overhead) + Storage RLS for writes (users can only upload to their own folder). Read access without auth is fine for user videos in this context since the URLs are not guessable.

**Why Supabase writes live on the frontend:**
When a Supabase JS client runs in the browser, it automatically attaches the user's JWT (from their active session) to every request. This means database RLS policies apply naturally — no extra work to scope writes to the current user. If the writes were on the backend instead, the backend would need to either receive the JWT from the frontend and create a user-scoped client per request, or use the service role key (which bypasses all RLS and is a security risk). Keeping writes on the frontend is simpler and safer.

**De-duplication of signal events:**
Merge all detected events into one time-sorted list (`[(index, "bottom"), (index, "top"), ...]`), then walk through it. If two consecutive events are the same type ("bottom, bottom"), replace the first with the second (keep the later, more committed one). The result is a strictly alternating sequence, which is the correct structure for pairing bottom→top rep cycles.

### Decisions made

**Column-based layout over tier-based:**
Tier-based (grouping skills by depth) is simpler but visually incorrect — one H-connector spanning an entire row regardless of actual prerequisites. Column-based requires more graph analysis but draws correct connectors where every skill connects visually to its own prerequisite. The added complexity is justified because accurate prereq connections are the whole point of a skill tree.

**20 skills across 4 tracks — exercise selection:**
As an advanced calisthenics practitioner, I chose exercises that form genuine biomechanical progression chains. The handstand is a prerequisite for the handstand push-up because you cannot press overhead without first controlling the balance. The domain knowledge makes every prerequisite edge defensible in an interview rather than arbitrary.

**Unique `order_in_track` for left-to-right column ordering:**
Within a row of branches, left-to-right order is controlled by `order_in_track` in Supabase. Using unique values makes ordering deterministic — PostgreSQL does not guarantee stable ordering for ties, so shared values caused non-deterministic rendering.

**Frontend owns all Supabase writes:**
See "What I learned" above. The backend stays as a pure stateless analysis API — it takes a video, returns JSON, knows nothing about users or database state.

**`pass_threshold` is stored per skill in the database:**
Rather than hardcoding "all checks must pass" in the frontend, the threshold is a float (0–1) on the `skills` table. This allows skills to be more lenient than 100% (e.g., 0.75 means 3 of 4 checks must pass) without any code change — just update the value in Supabase.

**Stretch goals deferred: Claude API feedback + demo videos on nodes:**
Originally in the MVP plan. Both were cut to scope: Claude API integration adds latency and cost without changing the pass/fail verdict, and filming demo videos for 20 skills is significant one-time work that isn't needed to demonstrate the core loop. Both are tracked as stretch goals for post-MVP.

### What's next
- Deployment: frontend to Vercel, backend to Railway or Render

---

## Step 8b — Demo videos + clickable locked nodes (stretch goal)
*Date: June 2026*

### What I built
- All three skill node states (locked, unlockable, unlocked) now open the skill modal on click — previously locked nodes did nothing when clicked
- `SkillModal` accepts a new `skillState` prop (`'locked' | 'unlockable' | 'unlocked'`) and renders differently for each state:
  - **Locked**: shows demo video (if `demo_video_url` is set), no filming instructions, a disabled "Locked" button
  - **Unlockable**: shows demo video (if set) above filming instructions, active upload button — existing behaviour preserved
  - **Unlocked**: shows user's own stored video, filming instructions, upload button for re-attempt — existing behaviour preserved
- `demo_video_url` is already a column on the `skills` table and is read directly from the Supabase row — no schema changes required
- The `demo-videos` storage bucket already existed as public from Step 7 — no infrastructure changes required
- Adding a demo video for any skill requires no code: upload to Supabase Storage → copy public URL → paste into `demo_video_url` for that skills row

### What broke / what was hard
Nothing broke. The key insight was that everything needed was already in place — the DB column, the public bucket, and the `getSkillState()` function in `TrackPage` that already computed `'locked' | 'unlockable' | 'unlocked'`. The change was purely about threading that value into `SkillModal` and branching the render logic on it.

### What I learned

**Prop drilling a computed value vs re-deriving it:**
`getSkillState(skill)` already existed in `TrackPage` and was used to set visual styles on each `SkillNode`. Rather than duplicating the locked/unlockable/unlocked logic inside `SkillModal`, the cleaner approach is to compute it once at the source (TrackPage, which owns the data) and pass it down. `SkillModal` shouldn't need to know about `unlockedIds` or prerequisite maps — it just needs to know the state it's displaying. This is the principle of "lift state, not logic" — the data lives where it's computed, and components further down the tree receive only what they need.

**Conditional rendering with three states:**
When a component has three meaningfully different appearances (not just "show or hide"), the clearest pattern is explicit state comparisons rather than boolean flags:
```jsx
{skillState === 'unlocked' && ...}   // exact match for one case
{skillState !== 'unlocked' && ...}   // everything else
{skillState === 'locked' ? ... : ...}  // branch between locked and non-locked
```
This is more readable than `isLocked`, `isUnlocked`, `isUnlockable` boolean props — you'd need to handle the impossible case where two are true simultaneously, and the JSX becomes harder to follow.

### Decisions made

**Show demo video for unlockable state too, not just locked:**
The demo video is "here's what the skill looks like when done correctly." A user who is about to attempt the skill benefits from watching it just as much as a user who can't attempt it yet. Hiding the demo from unlockable nodes would mean it disappears the moment a prerequisite is met, which is the wrong time to remove it.

**No filming instructions for locked skills:**
Showing filming instructions ("film from the side, full body visible") to someone who cannot attempt a skill yet is noise — it creates the false impression that they're about to do something. Hiding it keeps the locked modal focused: "here's what this skill is, here's what it looks like, come back when you've unlocked the prerequisites."

**`demo_video_url` null-safety is implicit:**
The demo video section only renders when `skill.demo_video_url` is truthy. No special handling is needed for skills without a demo video yet — the section simply doesn't appear. This means skills can be added to Supabase and filmed at different times without any "placeholder" state needed in the UI.

### What's next
- Deployment: frontend to Vercel, backend to Railway or Render

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
<!-- Fill in what you actually attempted -->

Planned stretch goals (attempt if time allows):
- **LLM narrative feedback** — use the Claude API to turn the structured pass/fail checks into a short paragraph of natural language coaching, e.g. "Your bottom position is solid but you're not quite locking out at the top — focus on driving your elbows down at the peak of each rep." More human than a list of pass/fail cards.
- **More exercises** — extend form analysis to squat (for the legs track) and L-sit / toes-to-bar (for the core track). Each needs its own set of landmark-based checks.
- **UI polish — game feel**
  - Skill nodes as shaped cards or hexagons rather than plain rectangles
  - Skill illustration or icon on each node instead of (or alongside) the text name
  - Unlock animation — particle effect or colour burst when a skill is unlocked
  - Smoother transitions between locked/unlockable/unlocked states

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
| Manual local extrema for rep detection | scipy.signal.find_peaks | Avoids adding a dependency; the simple loop is easy to explain in an interview |
| Average left+right elbow angle for rep signal | Single-arm angle | Robust to both side-on and front-facing camera angles |
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


