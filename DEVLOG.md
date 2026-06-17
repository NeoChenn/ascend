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

## Step 8c — Claude LLM narrative feedback (stretch goal)
*Date: June 2026*

### What I built
- `backend/services/llm_service.py` — calls the Claude API (`claude-haiku-4-5`) with the structured form check results and returns a 2–3 sentence coaching paragraph. The prompt formats each check as a PASS/FAIL bullet and asks for plain-prose feedback. Wrapped in `try/except` so a failed API call never breaks the upload response — returns `None` on any error.
- Updated `backend/main.py` to call `generate_narrative_feedback` after analysis and add a `narrative` field to the response JSON.
- Updated `SkillModal` to display the narrative in an italic box between the verdict banner and the check cards. The box only renders when `result.narrative` is non-null — the UI degrades gracefully when the API is unavailable.
- Added `anthropic` to `requirements.txt`.

### What broke / what was hard

**Wrong package — `google-generativeai` is deprecated:**
The first install used `google-generativeai`, which immediately showed a `FutureWarning` saying all support has ended. Switched to the replacement package `google-genai` (v2.x), which has a different API pattern: `genai.Client(api_key=...)` instead of `genai.configure(...)` + `GenerativeModel(...)`.

**`gemini-2.0-flash` not on free tier (`limit: 0`):**
The first model tried was `gemini-2.0-flash`. Got a 429 with `limit: 0` — not "you've run out" but "your quota is set to zero." Switched to `gemini-1.5-flash` since it's the documented free model.

**`gemini-1.5-flash` not found (`404 NOT_FOUND`):**
The new `google-genai` SDK defaults to API version `v1beta`. `gemini-1.5-flash` is only available in `v1`. Added `http_options=types.HttpOptions(api_version="v1")` to the client. Still 404 — it turned out `gemini-1.5-flash` isn't in this API key's model list at all (confirmed by running `client.models.list()`). The available text generation models were all `gemini-2.x` variants.

**`gemini-2.0-flash-lite` — quota still `limit: 0`:**
Switched to `gemini-2.0-flash-lite` (which appeared in the model list). Same `limit: 0` error. Root cause: the original API key was created in a project on **"Tier 1 · Prepay"** billing (visible in AI Studio → API Keys → Billing Tier column). Creating a new API key in a new project didn't help — the Google account itself has `limit: 0` on free tier quotas for all Gemini models, likely due to prior billing activity on the account.

### What I learned

**The `google-generativeai` → `google-genai` migration:**
The old package used a global `genai.configure(api_key=...)` call that set state for the entire module, then `GenerativeModel(model_name)` to create a model object, then `model.generate_content(prompt)`. The new package uses a stateless `Client` object: `client = genai.Client(api_key=...)`, then `client.models.generate_content(model=..., contents=...)`. The new pattern is cleaner — no global state, easier to test and reason about.

**API versioning in Google's AI platform:**
Google maintains multiple API versions simultaneously (`v1`, `v1beta`, `v1alpha`). Stable models graduate from beta to v1. Experimental models only appear in v1beta. The `google-genai` SDK defaults to v1beta to give access to the latest experimental models — but this means stable models that were retired from v1beta are no longer accessible with the default config. The `HttpOptions(api_version=...)` override selects which surface you're targeting.

**`limit: 0` vs rate limit exceeded:**
A 429 error with a `limit` value in the error body means two different things depending on the value:
- `limit: N` (where N > 0) — you've hit your quota, wait and retry
- `limit: 0` — the quota is set to zero for your account/project, retrying won't help

The second case is an account configuration issue, not a transient error. The `try/except` in `llm_service.py` handles both the same way — the narrative is just omitted — which is the right call: an LLM enhancement should never block the core feature.

**Graceful degradation as a real design principle:**
The `try/except` returning `None` means the entire upload flow (video analysis, skeleton overlay, pass/fail verdict, Supabase writes) continues to work even if the Claude API is completely unavailable. The frontend `{result.narrative && <p>...</p>}` pattern means nothing renders when `narrative` is null — no empty boxes, no error messages, no broken layout. This was the right architecture decision: the LLM is an enhancement, not a dependency.

### Decisions made

**`generate_narrative_feedback` in its own service file:**
Mirrors the existing pattern: `pose_service.py` owns MediaPipe, `analysis/` owns angle logic, `llm_service.py` owns the Claude API. `main.py` stays as a thin router that composes the services. This makes the LLM call easy to swap out (different provider, different model) without touching the route handler.

**Narrative positioned between verdict and check cards:**
The verdict banner gives the instant "pass/fail" read. The narrative adds context. The check cards give the specifics. This ordering goes from high-level to detailed — a natural reading order. Putting the narrative after the cards would bury it below a long list.

**Current status:**
The feature is implemented and the code is correct — the `try/except` means the app works with or without a working Claude API key. Switched from Gemini to the Anthropic SDK (`claude-haiku-4-5`) to avoid the Google free-tier quota issues encountered during development.

### What's next
- Deployment: frontend to Vercel, backend to Railway or Render

---

## Step 8d — UI polish & RPG feel
*Date: June 2026*

### What I built

**Navigation & labelling improvements:**
- Track switcher pill-bar on every track page — clicking Push/Pull/Core/Legs navigates directly between trees without going back to the landing page. Tabs use the track colour when active, grey when inactive. Styled to match the God of War skill tree reference.
- Renamed "Skill Tree" → "Skill Trees" (the page shows a body silhouette, not a tree), renamed track page titles from "{Label} Track" → "{Label} Tree"
- Back link on track pages restyled as a pill matching the tab switcher — same uppercase font, same border treatment, so the whole top bar reads as one cohesive nav unit
- Removed skill count subtitle ("3 skills") from track pages — added noise without useful information
- Increased pill font size from 0.62rem to 0.75rem after visual review

**Skill node icons:**
- Created `SkillIcons.jsx` — 21 hand-drawn SVG stick-figure icons, one per skill in the database. Every path uses `stroke="currentColor"` or `fill="currentColor"` so the icon colour inherits from the parent element's CSS `color` property. This means a single icon component automatically adjusts to locked (dark grey), unlockable (track colour), and unlocked (white) states with no extra logic — CSS propagates the colour for free.

**Glow and animation polish:**
- Unlock burst animation fires 1 second after the modal closes (was immediate). The delay lets the modal disappear and the page settle before the node pulses — feels more intentional.
- Added `autoPlay muted playsInline` to all four `<video>` elements in SkillModal. `muted` is required — browsers block autoplay on any video with audio unless it is explicitly muted.
- Unlocked skill nodes now glow with a layered `box-shadow` corona: a tight inner glow at 10px, a medium spread at 24px, and a wide outer halo at 48px, all using the track colour.

**3-level connector colours:**
- Connectors now reflect the state of the skill they lead *into*: full track colour (unlocked), track colour at 67% opacity (unlockable), flat `#3a3a3a` grey (locked). This means the path you've already cleared is visually distinct from the path ahead.
- Unlocked connectors also get a `box-shadow` glow, making cleared paths look like lit energy conduits.

**RPG design overhaul:**
- Added Google Fonts: **Bebas Neue** for page titles (bold condensed, immediately reads as "game UI"), **Rajdhani** (weights 500 and 700) for all body/tab/nav text (angular, clean at small sizes). One `@import` in `index.css`, two `font-family` changes.
- Added a vignette overlay to the body background: a fixed `radial-gradient` darkens the page edges while the dot grid scrolls underneath. Uses `background-attachment: fixed, scroll` so the two layers move independently — the vignette stays anchored to the viewport.
- Navbar background set to `#141414` — slightly lighter than the `#0f0f0f` page background to visually separate it as a distinct layer.
- Dot-grid background moved from `TrackPage.module.css` to `index.css` (global `body`) so all pages share it.

**What didn't work — octagonal nodes:**
Attempted to change skill nodes from circles to cut-corner octagons using `clip-path: polygon(...)`. The shape itself rendered correctly. However, `box-shadow` is clipped by `clip-path` — the shadow is drawn inside the clipping region and then cut, making the glow completely invisible. Switched to `filter: drop-shadow()` instead, which is applied *after* clipping and should follow the polygon outline. In practice, `drop-shadow` was still not visually detectable on these nodes inside flex columns, even at high blur values. Reverted to circles and restored `box-shadow` — the glow was immediately visible again. The `clip-path + filter: drop-shadow` combination is theoretically correct but seems to not composite as expected inside deeply nested flex layouts in practice.

### What broke / what was hard

**Clip-path clips box-shadow (and drop-shadow didn't save it):**
`clip-path` clips the entire painted layer of an element, including `box-shadow`. Even though `filter: drop-shadow` is documented to apply after clipping, it failed to produce a visible glow in this context. Root cause is unclear — possibly a compositing layer or stacking context issue created by the surrounding flex structure. Lesson: if you need a visible outer glow on a clipped shape, test it early. The safest approach is to put the glow on a *wrapper* element that has no `clip-path`, and the clip-path on the inner element.

**`Object.entries` ordering for the track switcher:**
JavaScript objects preserve insertion order for string keys in all modern engines. `Object.entries(TRACK_LABELS)` iterates in definition order, so the tab sequence (Push → Pull → Core → Legs) matches the source code order. This is a reliable modern JS behaviour, but worth knowing — it wasn't guaranteed in older specs.

### What I learned

**`currentColor` as a CSS variable:**
SVG elements that use `stroke="currentColor"` or `fill="currentColor"` inherit the nearest ancestor's CSS `color` value. This means you can control icon colour entirely from CSS without touching SVG attributes — set `color: trackColor` on the parent div and every stroke in the icon updates. It's the standard pattern for icon libraries and avoids duplicating colour logic between CSS and SVG.

**`background-attachment: fixed` for viewport-anchored backgrounds:**
Setting a background layer to `fixed` makes it position relative to the viewport, not the element. This means as the user scrolls, the vignette gradient stays in place and the dot grid scrolls underneath it — the two layers move at different rates from the same `background-image` declaration. Only one `background-attachment` value is needed for two layers: `background-attachment: fixed, scroll`.

**Google Fonts `display=swap`:**
Adding `&display=swap` to the Google Fonts import URL tells the browser to use a fallback system font while the custom font loads, then swap it in when ready. Without this, the browser may show invisible text ("FOIT" — flash of invisible text) during font download. `swap` avoids FOIT at the cost of a brief layout shift when the font arrives.

**Why `muted` is required for video autoplay:**
Browsers enforce a policy that prevents audio from playing without a user gesture. A `<video>` element with `autoPlay` but no `muted` attribute will silently fail to autoplay on Chrome and Safari. Adding `muted` tells the browser the video has no audio that could surprise the user, which satisfies the policy. `playsInline` prevents iOS Safari from forcing the video into fullscreen mode.

### Decisions made

**Connector colour rule: brightness follows the skill above, not below:**
Each connector's colour is determined by the state of the skill it leads *into* (the child/dependent skill above it in the layout). This means a connector is bright only when the destination is already unlocked — it tells you where you've been. An alternative (colour based on the skill below/prerequisite) would make connectors bright once the prerequisite is met, indicating what's possible — but that creates visual clutter when many skills are unlocked. The "where you've been" rule feels more earned.

**Bebas Neue for titles only, Rajdhani for everything else:**
Using Bebas Neue for body text would be unreadable at small sizes — it's a display font. Rajdhani is designed to be legible at small sizes while still having an angular game-UI feel. The combination gives visual hierarchy: Bebas Neue signals "this is an important label" for headings, Rajdhani keeps the rest of the UI readable.

**Revert octagonal nodes rather than debug the glow:**
The octagonal shape looked good in isolation, but without the glow the nodes lost their most visually distinctive state indicator. The glow communicates "unlocked" at a glance, especially in a dark UI where colour alone can be subtle. Shape differentiation (octagon vs circle) matters less than the glow. Chose the working glow over the novel shape.

### What's next
- Deployment: frontend to Vercel, backend to Railway or Render

---

## Step 9 — Deployment prep
*Date: June 2026*

### What I built

Three code changes to make the app deployable, plus a round of housekeeping:

- Replaced the hardcoded `http://127.0.0.1:8000/upload` URL in `SkillModal.jsx` with `${import.meta.env.VITE_API_URL}/upload`. Added `VITE_API_URL=http://127.0.0.1:8000` to `frontend/.env.local` so local dev is unchanged.
- Made the backend CORS origin configurable: `main.py` now reads `FRONTEND_URL` from the environment (`os.getenv("FRONTEND_URL", "http://localhost:5173")`) instead of hardcoding localhost. Added `FRONTEND_URL=http://localhost:5173` to `backend/.env` for local dev.
- Created `frontend/vercel.json` with a SPA rewrite rule — without it, navigating directly to a route like `/track/push` would return a 404 from Vercel because no file at that path exists on disk.
- Deleted the legacy `Upload.jsx` and `Upload.module.css` (the generic upload page replaced by the skill modal flow), removed its import and `/upload` route from `App.jsx`.
- Deleted dev test HTML files and screenshots from `frontend/public/`.
- Fixed the browser tab title from `"frontend"` to `"Ascend"` in `index.html`.
- Added `shape.png` favicon and per-skill icon PNGs to `frontend/public/`.

The app is now ready to deploy: push to GitHub → Railway (backend) → Vercel (frontend) → wire env vars between them.

### What I learned

**Environment variables have two distinct uses, not just one:**

The common mental model is "env vars store secrets." That's true, but incomplete. They have a second use: **configuration that differs between environments**. The same codebase needs to behave differently on a developer's laptop vs on a production server — pointing at a local backend vs a hosted one. An env var handles this cleanly.

The two uses side by side:

| Use | Example | Why env var |
|---|---|---|
| Keep secrets private | `SUPABASE_ANON_KEY`, `ANTHROPIC_API_KEY` | Never commit credentials to Git |
| Configure per environment | `VITE_API_URL`, `FRONTEND_URL` | Same code, different values on laptop vs production |

`VITE_API_URL` is not a secret — anyone can open DevTools and see the URL. The reason it's an env var is purely so you don't have to change source code when deploying. Hardcoding the Railway URL directly would break local dev; hardcoding localhost would break production.

**The `VITE_` prefix is a security mechanism in Vite:**
Vite only exposes variables prefixed with `VITE_` to the browser bundle. Any env var without that prefix is intentionally hidden — it never leaves the build tool. This means you can safely have both `VITE_API_URL` (intentionally public) and `SUPABASE_SERVICE_KEY` (intentionally hidden) in the same `.env` file — Vite knows which ones the browser is allowed to see.

**`.env` files are just a local convenience:**
On Railway and Vercel, there are no `.env` files — you enter variables through the dashboard UI, and the platform injects them into the running process at startup. The app calls `os.getenv()` or `import.meta.env.VITE_*` and doesn't care whether the value came from a file or a dashboard. `.env` files are a developer ergonomics tool for local work.

**CORS is a browser rule, not a server rule:**
CORS (Cross-Origin Resource Sharing) only applies to requests made from a browser. When JavaScript at `ascend.vercel.app` calls an API at `ascend-backend.railway.app`, the browser sees two different domains ("origins") and blocks the request unless the API explicitly says it's allowed. The server's `allow_origins` list is that permission declaration. The backend wasn't going to work in production with `allow_origins=["http://localhost:5173"]` — the Vercel URL would be rejected even with a correct API URL.

**React Router + Vercel: the SPA routing problem:**
Vite builds the app into static files — just `index.html`, CSS, and JS. Vercel serves those files from a CDN. When you visit `ascend.vercel.app`, Vercel serves `index.html` and React Router takes over all navigation in the browser. The problem is *direct URL access*: if a user goes straight to `ascend.vercel.app/track/push`, Vercel looks for a file at `track/push/index.html` on disk — that file doesn't exist, so Vercel returns a 404. The `vercel.json` rewrite rule tells Vercel to serve `index.html` for any URL and let React handle the routing.

**`os.getenv("VAR", "default")` as a safe fallback pattern:**
`os.environ["VAR"]` raises a `KeyError` if the variable is missing. `os.getenv("VAR", "default")` returns the default instead. For the CORS origin, `"http://localhost:5173"` as the default means: if `FRONTEND_URL` is not set in the environment, fall back to localhost — local dev works with no extra config.

### Decisions made

**Vercel for frontend:**
Vercel is purpose-built for frontend deployment and has first-class support for Vite/React. Free tier, connects directly to GitHub, and auto-deploys on every push to main. The only required config was `vercel.json` for SPA routing. Zero build configuration needed — Vite preset is detected automatically.

**Railway for backend:**
Railway supports Python/FastAPI directly from a GitHub repo, handles `requirements.txt` automatically, and injects `$PORT` into the environment so uvicorn can bind to the right port. Free tier is enough for a portfolio project with low traffic.

**Deploy backend before frontend:**
The frontend needs to know the backend's URL (`VITE_API_URL`) before Vercel builds it — this value is baked into the compiled JS bundle at build time. Railway deploys first, generating the URL, then Vercel uses that URL as a build-time env var.

### What's next
- Complete the Railway + Vercel deployment (dashboard steps, not code steps)
- Film and upload demo videos for skill nodes once the app is live

---

## Step 9b — Deployment: crashes and fixes
*Date: June 2026*

### What happened

After the code changes in Step 9, deploying to Railway produced five distinct crashes — each one revealing a new problem only after the previous one was fixed. This entry documents every error, its cause, and what fixed it.

---

**Crash 1: Railway ignoring `nixpacks.toml` — couldn't install system libraries**

The initial plan was to use `nixpacks.toml` to specify system libraries (like `libxcb`) that OpenCV needs on a headless server. This file was silently ignored. Root cause: Railway had switched its default builder from Nixpacks to a newer tool called **Railpack**. Railpack reads its own config format, not `nixpacks.toml`.

Railpack is a "smart" builder — it auto-detects Python projects, installs `requirements.txt`, and starts the server. But it gives no way to install arbitrary OS-level packages. The escape hatch is a **Dockerfile**: when Railway detects a `Dockerfile` in the repo root, it stops using Railpack entirely and just executes the Docker instructions. This gives full control over the build environment. Lesson: when a deployment platform's auto-detection doesn't support your dependencies, a Dockerfile is always the override.

---

**Crash 2: `libxcb.so.1: cannot open shared object file`**

Once running via Dockerfile, the first library error appeared: `opencv-python` requires X11 display libraries (`libxcb`, `libGL`, etc.) because it was compiled with full GUI support. A Railway container has no display. Fix: switch to `opencv-python-headless` in `requirements.txt` — this is the same library compiled without the display stack, intended for servers.

---

**Crash 3: `$PORT` is not a valid integer**

Railway injects the HTTP port as a `$PORT` environment variable. The Dockerfile `CMD` was:
```
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```
The JSON array form of `CMD` bypasses the shell entirely — `$PORT` is passed as the literal string `"$PORT"` rather than being expanded. Uvicorn tried to parse `"$PORT"` as an integer and crashed. Fix: wrap in `sh -c` so a shell handles the substitution:
```
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```
The `${PORT:-8000}` syntax also provides a local fallback: if `PORT` is unset (e.g. during local Docker testing), it defaults to 8000.

---

**Crash 4: `POST //upload` returning 404**

After the backend was running, video uploads from the Vercel frontend returned 404. Railway logs showed `POST //upload` — a double slash. The cause: `VITE_API_URL` on Vercel had been set with a trailing slash (`https://ascend-production-515a.up.railway.app/`). In `SkillModal.jsx`, the URL is constructed as `` `${import.meta.env.VITE_API_URL}/upload` ``, which produced `…railway.app//upload`. Fix: remove the trailing slash from the Vercel env var and redeploy Vercel (required because `VITE_` variables are baked into the JS bundle at build time, not read at runtime).

---

**Crash 5 (series): `libGLESv2.so.2`, `libEGL.so.1` — MediaPipe C bindings missing graphics libraries**

The hardest set of errors. MediaPipe ships a pre-compiled C shared library (`libmediapipe_tasks_c.so`). This binary was compiled on a full desktop Linux with GPU support. When Python loads MediaPipe, the OS reads the binary's dependency list and tries to open every `.so` on it — OpenGL ES, EGL, Vulkan, GBM — **immediately at load time**, before any Python code runs.

A previous fix had added `delegate=mp_python.BaseOptions.Delegate.CPU` to force CPU inference — this routes computation through the CPU rather than the GPU. But this flag only controls which compute *path* MediaPipe takes. The binary still has GPU library names in its link table, and the OS still tries to open them. If even one `.so` is missing, the load fails with `OSError`.

`python:3.13-slim` is a minimal image that includes nothing but Python. Every graphics library was missing. They had to be installed via `apt-get` in the Dockerfile. The errors appeared one at a time because the dynamic linker reports only the first missing dependency:

| Error | Package installed | What it provides |
|---|---|---|
| `libGLESv2.so.2` | `libgles2` | OpenGL ES (GLES) — embedded GPU rendering API |
| `libEGL.so.1` | `libegl1` | EGL — interface between OpenGL and the OS window system |
| (proactively) | `libvulkan1` | Vulkan — modern GPU compute API |
| (proactively) | `libgbm1` | GBM — Generic Buffer Management, off-screen rendering surfaces |

After adding all four, MediaPipe loaded successfully and the upload endpoint worked end-to-end.

---

### What I learned

**Dynamic linking — the key concept behind all the `.so` errors:**
When a compiled binary (`.so` or executable) is built, the compiler records the names of every shared library it uses — this list is called its *dynamic dependencies*. When the OS loads the binary, it resolves all those names to actual files on disk immediately, before executing any code. If a file is missing, the load fails with `OSError: libXxx.so: cannot open shared object file`. This is called *dynamic linking*, and it's why a library built on Ubuntu Desktop can fail to load on a Docker slim image — the slim image has none of the desktop libraries.

**The difference between `docker-slim` and a desktop Linux environment:**
`python:3.13-slim` deliberately removes everything not needed to run Python — including all graphics, display, and GPU libraries. These exist on every desktop Linux by default (because users have monitors and apps need to render things). A headless server never needs them unless it runs ML libraries like MediaPipe that were compiled with GPU support baked in. The Dockerfile's `apt-get install` is how you put them back.

**Platform-as-a-Service vs Dockerfile:**
PaaS builders (Railpack, Heroku buildpacks) are a convenience trade-off — zero config for standard apps, but limited control over the underlying OS environment. A Dockerfile is always the escape hatch and is supported by every container platform. For any Python project with unusual system dependencies (MediaPipe, OpenCV, video processing), a Dockerfile is the reliable path.

**`VITE_` variables are baked into the bundle at build time:**
Unlike server-side env vars which are read when the process starts, Vite inlines `VITE_*` variables directly into the compiled JavaScript bundle at build time. This means changing a `VITE_` variable in the Vercel dashboard requires a full redeploy — the old bundle is still serving the old URL until a new build runs.

### What's next
- Film and upload demo videos for skill nodes
- Add form analysis for more exercises (squat, L-sit)

---

## Step 10a — Legs track form analysis (Squat, Bulgarian Split Squat, Pistol Squat)
*Date: June 2026*

### What I built

Three new analysis files — one per skill in the legs track — plus two additions to `_shared.py` and a refactor of the `/upload` dispatch in `main.py`.

**Shared utilities added to `_shared.py`:**
- `_compute_knee_angles()` — analogous to `_compute_elbow_angles()` from Steps 5/6. Computes the average hip-knee-ankle angle for both legs per frame, using landmarks 23/25/27 (left) and 24/26/28 (right).
- `_check_torso_upright()` — checks that the torso stays within 45° of vertical at the bottom frames of a squat movement. Different from `_check_body_alignment` (which checks shoulder→hip→knee sag in a plank position) — see Decisions section.

**New analysis files:**

- `backend/services/analysis/squat.py` — three checks: depth (knee < 100° at bottom), lockout (knee > 155° at top), torso upright at bottom frames.
- `backend/services/analysis/bulgarian_split_squat.py` — three checks: front-knee depth (< 105°), rear knee descent (rear knee must go below the elevated rear foot level), torso upright. Also identifies which leg is the working leg.
- `backend/services/analysis/pistol_squat.py` — three checks: depth (knee < 80° — stricter than squat), lockout, free leg extension (free leg must be held straight forward, hip-knee-ankle > 150°). Also identifies working leg.

**`main.py` refactor:**
Replaced the `if exercise == "push_up" … else … pull_up` chain with a `ANALYSERS` dict mapping exercise names to functions. Adding a new exercise now only requires touching that dict. Also fixed a latent bug: if `exercise` had no analyser (a skill with `analysis_key = null`), the old code would silently run pull-up analysis instead. The new code sets `feedback = None` and `narrative = None`, which is honest.

**Supabase:**
Set `analysis_key` to `"squat"`, `"bulgarian_split_squat"`, and `"pistol_squat"` for the three legs skills — the whole track is now unlockable end-to-end.

### What I learned

**Working leg identification — the min() trick:**
For BSS and pistol squat, I need to know which leg is the working leg before I can check its depth, but I also need the depth signal to detect where the bottom frames are. This is a chicken-and-egg problem. Solution: use `min(left_knee_angle, right_knee_angle)` per frame as the rep-tracking signal. The working (more bent) leg will always produce the smaller angle, so the minimum reliably tracks it without knowing which leg it is in advance. Then, once bottom frames are detected, I look at which leg had the smaller angle at those frames — that's the working leg.

**Torso lean vs hip sag — why a new check was needed:**
`_check_body_alignment` from Steps 5/6 measures the shoulder→hip→knee angle, which detects hip sag in a plank (push-up or pull-up body position). For a squat, this angle is *supposed* to change — the person is bending. What we actually want for a squat is to measure how much the torso (shoulder→hip vector) deviates from vertical. These are geometrically different questions that happen to use the same joints, which is why a new function was needed rather than reusing the existing one.

**Why check torso lean only at bottom frames:**
If you average torso lean across the entire video, the standing portions (where lean ≈ 0°) drag the average down and mask a genuinely excessive lean at the bottom. The bottom of the squat is where forward lean is worst and most relevant to form, so that's where to check.

**Implementation note — rep detection for squats is the inverse of pull-ups:**
A pull-up has a local MAX at the bottom (arms straight, ~180°) and a local MIN at the top (arms bent, ~60°). A squat has a local MAX at the top (knees straight, ~170°) and a local MIN at the bottom (knees bent, ~80–100°). The algorithm is identical (see Step 5); only which extreme is "bottom" vs "top" changes. A regular squat uses < 100° for the bottom threshold; a pistol squat uses < 80° because it demands deeper knee flexion.

### Decisions made

**Implement bottom-up within the prerequisite chain:**
The decision to start with Squat (rather than Pistol Squat, which is more interesting) was deliberate. Pistol Squat has Bulgarian Split Squat as a prerequisite, which has Squat as a prerequisite. If Squat has no analysis, users can never unlock it, which means the Bulgarian Split Squat is permanently locked, which means Pistol Squat is permanently locked. Analysis in the wrong order produces dead code.

**105° threshold for BSS depth (vs 100° for squat):**
The elevated rear foot limits hip mobility slightly compared to a bilateral squat — reaching exactly 90° of front-knee flexion is harder and less important than in a regular squat. 105° is lenient enough to reward a genuine lunge without penalising the ROM difference.

**`_identify_working_leg` kept local to each file, not added to `_shared.py`:**
The function is identical in `bulgarian_split_squat.py` and `pistol_squat.py`, which looks like a duplication. But it's a tiny helper (10 lines), and more importantly, `_shared.py` is for truly general utilities that work across exercise types (angle calculation, smoothing, sag check). "Which leg is working" is conceptually specific to split/single-leg movements. Keeping it in each file avoids making the shared module carry exercise-specific logic.

**Rear knee descent check — binary, not angle-based:**
Initially I considered measuring the rear knee angle in a BSS. But this is unreliable: the rear knee angle changes with both depth AND bench height, and the bench height is unknown. Instead, the check asks: "is the rear knee lower than the elevated rear ankle?" This is a stable geometric fact regardless of bench height — if the knee is below the foot level, the person has genuinely descended.

### What's next
- Film demo videos for skill nodes

---

## Step 10b — Core track form analysis (Leg Raise, Toes to Bar, L-sit, One-arm Toes to Bar)
*Date: June 2026*

### What I built

Four new analysis files for the core track, plus two new shared utilities.

**Shared utilities added to `_shared.py`:**
- `_compute_hip_angles()` — the primary signal for all core exercises. Computes the shoulder-hip-ankle angle per frame, averaged across both sides. At hanging rest this is ~180° (body straight); at horizontal it's ~90°; at a full toes-to-bar pike it's <45°. One function covers all three rep-based exercises (see Step 10a for how `_compute_knee_angles` was the equivalent for legs).
- `_check_leg_straightness()` — checks that the knee angle is > 150° at the top of the movement. Shared between `leg_raise.py` and `toes_to_bar.py` to avoid duplication.

**`leg_raise.py`:** Rep detection using `_compute_hip_angles` (local MAX = hanging, local MIN < 110° = legs at horizontal). Three checks: height reached, leg straightness, no swinging.

**`toes_to_bar.py`:** Same rep structure as leg raise but stricter top threshold (local MIN < 60° — a full pike to touch the bar). Height check uses y-coordinate comparison rather than angle (see Decisions).

**`lsit.py`:** Fundamentally different — a static hold with no rep detection. All three checks average across the entire video. `rep_count` is always 0.

**`one_arm_toes_to_bar.py`:** Imports and reuses the rep detection and check functions from `toes_to_bar.py` directly. The only change is the exercise name in the return dict (see Decisions).

### What broke / what was hard

Nothing broke. The patterns from Steps 5, 6, and 9c transferred cleanly — the main challenge was design, not debugging.

### What I learned

**The L-sit breaks the rep-counting pattern — and that's correct:**
Every previous exercise (pull-up, push-up, squat, leg raise, etc.) produces a wave signal — angle goes from a rest position, moves to a peak, and returns. The L-sit has no wave. The signal is (ideally) a flat line held near 90°. Trying to detect "reps" on a flat line would produce garbage. The right approach is to abandon the rep-detection architecture entirely for static holds and average across the whole video. `rep_count = 0` is honest: an L-sit is measured in seconds, not reps.

**Positional checks vs angle checks — when each is right:**
Every previous check has been angle-based (is this joint bent enough?). The toes-to-bar height check is different: "did the toes reach the bar?" The bar is at wrist height — a fixed physical object. The angle of the hip joint can't tell you whether the toes touched the bar, because the bar's position in the frame varies per user and camera setup. A y-coordinate comparison (`ankle_y ≤ wrist_y`) answers the question directly, because the wrists are gripping the bar so they ARE the bar's position.

**Monitoring hips (not shoulders) for swing detection:**
The `_check_no_swing` function monitors hip y-position rather than shoulder y-position (which `_check_kipping` in `pull_up.py` uses). In a hanging leg raise, the hips are what swing — a hip jerk provides the momentum that drives the legs up. The shoulders stay relatively fixed because the hands are gripping the bar. Monitoring the wrong landmark would miss the actual swing.

### Decisions made

**One-arm Toes to Bar reuses Toes to Bar analysis wholesale:**
From a side camera, a one-arm toes to bar and a two-arm toes to bar are geometrically identical — the hip angle, the height reached, and the leg straightness are the same checks. Whether one or two hands are on the bar is not detectable via pose landmarks from the side. The decision: reuse all existing logic and rely on the user filming with the gripping hand clearly visible. This is an intentional "trust the user" tradeoff — the analysis confirms the form quality, not the specific grip variation. An alternative would be a front-facing camera to see both arms, but this would break every other check that requires a side view.

**Prerequisite chain determines implementation order:**
The order was: Leg Raise (entry point) → Toes to Bar and L-sit (both require Leg Raise) → One-arm Toes to Bar (requires Toes to Bar). This is the same bottom-up principle from Step 10a: implementing One-arm Toes to Bar before Toes to Bar would create dead code, since the skill can never be reached.

**`_check_leg_straightness` in `_shared.py`, not duplicated:**
Both `leg_raise.py` and `toes_to_bar.py` need the same knee-extension check at the top of the movement. Since it's used in two files and has no exercise-specific logic, it belongs in `_shared.py`. This is different from `_identify_working_leg` in the legs track (kept local) — that function had exercise-specific semantics. A check that simply asks "are the knees straight?" is genuinely general.

### What's next
- Film and upload demo videos for skill nodes
- Remaining push and pull track exercises (Explosive Pull-up, Muscle-up, Archer Push-up, etc.)

---

## Step 10c — Analysis accuracy fixes (L-sit hold duration + first-rep evaluation)
*Date: June 2026*

### What I built

Two correctness fixes to the form analysis system, plus a Supabase update and a small frontend change.

**L-sit: minimum consecutive hold duration**

The original `analyse_lsit` averaged all three metrics (hip angle, knee angle, elbow angle) across every frame in the video. This had a flaw: a user who briefly dipped into the position and then rested — or who was setting up for 2 seconds before a 1-second hold — could pass on the average even without a genuine hold.

Replaced averaging with a **consecutive-frame streak**: each frame is evaluated as a boolean (all three criteria met simultaneously?), then the longest unbroken run of True frames is found. If that streak is ≥ 90 frames (~3 seconds at 30 fps), the skill passes.

The three existing diagnostic cards (hip angle, leg extension, arm lockout) are kept unchanged — they still average across all frames and tell the user which individual criterion is failing. A fourth `hold_duration` card is added as the actual gate. The return dict includes a `hold_seconds` field so the frontend can display "3.3s held" instead of "0 reps detected."

**Dynamic analysers: first rep only**

All 8 dynamic analysers (pull-up, push-up, squat, BSS, pistol, leg raise, toes-to-bar, one-arm toes-to-bar) previously built `bottom_frames = [r[0] for r in reps]` — averaging checks over every detected rep. If a user filmed 3 reps and the third was notably worse, the average could fail them even if rep 1 was clean. Since the app is about demonstrating a skill (1 rep with good form is enough), this was wrong.

Fixed by evaluating only `reps[0]`:
```python
first_rep = reps[0]
bottom_frames = [first_rep[0]]
top_frames = [first_rep[1]]
```

The same 2-line change in each of the 8 files. `rep_count` is unaffected — it still counts all detected reps for display.

**Supabase filming instructions + frontend display**

Updated `filming_instructions` for all skills via SQL: dynamic skills now say "trim to just the rep, film one clean attempt"; L-sit says "trim to just your hold." This aligns the user instruction with the app's philosophy (skill demonstration, not rep counting) and with how the backend now evaluates the video.

`SkillModal.jsx` now reads `data.feedback.hold_seconds` from the response. If the field is present, it displays "Xs held" in place of the rep count label. For all non-static exercises, `hold_seconds` is absent and the existing "N reps detected" display is unchanged.

### What broke / what was hard

Nothing broke functionally — all imports passed and the synthetic test confirmed the streak logic worked correctly on first attempt.

### What I learned

**Averaging vs streak for static holds:**
Averaging across all frames is the right approach when every frame should look roughly the same (a static hold). The flaw was that "all frames" included frames where the person hadn't yet assumed the position. The streak approach doesn't require trimming the video perfectly — it just finds the longest valid window and ignores everything else. If the streak is 3 seconds, the user held for 3 seconds regardless of what happened before or after.

**AND-ing per-frame criteria before the streak is essential:**
If you run three separate streaks (one per metric) instead of one combined streak, you could pass a user whose hip angle was correct for 5 seconds but whose knees were bent the whole time. The AND ensures all three criteria are simultaneously correct — not three independent minimums. The `zip()` comprehension `[h < 100 and k > 155 and e > 155 for h, k, e in zip(hip, knee, elbow)]` is the concise way to express this.

**Multi-rep averaging creates unfair failures:**
Averaging across all detected reps seems reasonable — you'd want consistent form throughout. But in practice, users who film 2–3 reps will often have a noticeably worse final rep due to fatigue. "1 clean rep = pass" is the right semantic for a skills app (not a conditioning tracker), so the analysis should reflect that.

**`hold_seconds ?? null` as a per-exercise field discriminator:**
`hold_seconds` is only present in L-sit feedback. The frontend uses `?? null` coalescing to store it as null for all other exercises. A single ternary in JSX then handles both display cases — no exercise-type awareness needed anywhere else in the component.

### Decisions made

**3 diagnostic cards retained alongside hold_duration:**
A single "hold_duration" card would tell the user whether they passed but not why they failed. Keeping the hip/knee/elbow cards means a user who held for 1.2 seconds sees exactly which metric dropped — "your knees were bending throughout the hold" — giving them something to fix.

**First rep (not best rep):**
"Best rep" (the rep with the most extreme bottom position) would be the most lenient option. "First rep" is simpler to implement, has a clear justification (freshest effort, unaffected by fatigue), and pairs naturally with the filming instruction to film one clean attempt. For a portfolio project, simplicity and explainability win over marginal leniency.

**Filming instruction as the primary guardrail:**
Updating the instructions to say "one clean rep, no setup or rest" is the user-facing complement to the first-rep-only code change. The code handles the case where a user films a little extra anyway; the instruction sets the right expectation so they don't have to think about it.

### What's next
- Remaining push/pull track exercises (Explosive Pull-up, Muscle-up, Archer Push-up, etc.)
- Film and upload demo videos for skill nodes

---

## Step 10d — Pull track form analysis (Explosive Pull-up, Muscle-up, Archer Pull-up, Straddle Front Lever, One-arm Pull-up)
*Date: June 2026*

### What I built

Five new analysis files completing the entire pull track. Every pull track skill (6 of 6) now has automated form analysis — the full chain from Pull-up to One-arm Pull-up can be unlocked end-to-end.

**`explosive_pull_up.py`:**
Reuses pull-up rep detection and bottom-extension check. Replaces `_check_top_flexion` (chin-over-bar) with a new `_check_chest_to_bar` check: at the top frame, compare average shoulder y to average wrist y. In an explosive pull-up, the athlete pulls high enough that the chest reaches bar level — the shoulders should rise to the same height as the wrists (which are gripping the bar). Pass: `avg_wrist_y - avg_shoulder_y ≥ 0`. No kipping check — explosive momentum is the whole point.

**`muscle_up.py`:**
No rep detection. Two best-frame scans across all frames:
1. `pull_depth` — minimum elbow angle < 70°. A muscle-up requires pulling the elbows past the bar, demanding a tighter angle than a chin-over-bar pull-up (≈90°).
2. `above_bar_lockout` — any frame where `elbow_angle > 150°` AND `hip_y < wrist_y` (hips above bar). The dip transition isn't detected — too hard to isolate without knowing exact bar position — but if the athlete got above the bar with straight arms, the movement is complete.

**`archer_pull_up.py`:**
Per-side elbow tracking (not averaged). Compute `left_elbow_angles` and `right_elbow_angles` separately per frame. Rep detection runs on `min(left, right)` per frame — the working arm (more bent) always produces the smaller angle, so the minimum tracks the rep without knowing which arm is working. At the top frame: identify working arm (`min`) and assisting arm (`max`), then check working arm < 90° and assisting arm > 140°.

**`straddle_front_lever.py`:**
Static hold, same streak architecture as `lsit.py`. Per-frame criterion: body horizontal AND arms locked simultaneously. Body angle from horizontal is computed as `atan2(|hip_y - shoulder_y|, |hip_x - shoulder_x|)` — 0° = flat, 90° = hanging straight down. Pass: < 25°. Arms locked: elbow > 155°. Hold passes at ≥90 frames (~3s). Returns `hold_seconds` so the frontend displays "Xs held." The straddle leg position is not checked — indistinguishable from a full front lever from a side camera.

**`one_arm_pull_up.py`:**
Imports and reuses everything from `pull_up.py` wholesale (identical to `one_arm_toes_to_bar.py` pattern). Only the exercise name changes. From a side camera the geometry is identical — same elbow signal, same checks. The one-arm constraint is verified by the user filming with the gripping arm clearly visible.

**`__init__.py` and `main.py`:**
Added imports and `ANALYSERS` entries for all 5 new functions. Supabase `analysis_key` updated for all 5 skills.

### What broke / what was hard

Nothing broke. The patterns from previous steps transferred directly — the main challenge was deciding the right geometric check per exercise.

### What I learned

**Three distinct analysis patterns for one track:**
The pull track contains exercises that don't fit a single pattern. Explosive pull-up and archer pull-up are rep-based (same local-extrema signal detection as pull-up). Muscle-up requires no rep detection — the two key positions (deep pull and above-bar lockout) can be found by a global scan. Straddle front lever is a static hold. Recognising these as distinct patterns and matching each exercise to the right one made the implementation straightforward.

**The `min(left, right)` trick for asymmetric exercises:**
For exercises where only one side drives the movement (archer pull-up, BSS, pistol squat), using the minimum elbow/knee angle per frame as the rep signal solves a chicken-and-egg problem: you can't identify which side is working without detecting the rep, but you need the rep signal to find the working side. The minimum always reflects the working side, so the signal is valid regardless of which arm is pulling.

**Geometric discriminator: angle from horizontal vs angle from vertical:**
`_check_torso_upright` in `_shared.py` measures angle from vertical (useful for squats, where the torso should be nearly vertical). The front lever needs angle from horizontal (the body should be nearly horizontal). Both use `atan2` but swap the `dx` and `dy` arguments. Understanding this distinction up front prevented a subtle but serious bug — using the wrong formula would have had the check pass when the body was vertical (hanging) and fail when horizontal (correct position).

**What `muscle_up.py` can and can't check:**
The dip transition (elbow moving from below the bar to above it) is the hardest part of a muscle-up technically, but it's also the hardest part to detect from a side camera without knowing the exact bar y-coordinate. Two checks — pull depth and above-bar lockout — verify the start and end of the above-bar portion. If both pass, the movement is complete. A future improvement could estimate bar position from the wrist coordinates and use it as a reference for the transition frames, but for a portfolio project this level of verification is sufficient and explainable.

### Decisions made

**No kipping check for explosive pull-up:**
The standard pull-up check flags shoulder y-delta > 0.03 per frame as kipping. For an explosive pull-up, this threshold would fire almost immediately — the movement is *defined* by rapid upward acceleration. Omitting the check is correct: explosive momentum is the skill, not a form fault.

**`above_bar_lockout` uses a single boolean card, not a measurement:**
The check is binary — either a frame satisfying both conditions exists, or it doesn't. There's no meaningful scalar to report (no "how far above the bar"). `measurement: None` is honest. This is different from `pull_depth`, which reports the actual minimum elbow angle so the user knows how close they came.

**Straddle front lever threshold: 25° from horizontal (not 20°):**
The straddle position shifts the centre of mass forward compared to a full front lever, meaning the hips naturally sit slightly lower to counterbalance. A 20° threshold (borrowed from the plan) would be too strict for the straddle variant. 25° accommodates this without accepting a body position that's clearly not horizontal.

### What's next
- Push track exercises (Archer Push-up, Diamond Push-up, etc.)
- Film and upload demo videos for skill nodes

---

## Step 10e — Push track form analysis (Bent Arm Planche, Straddle Planche, Archer Push-up, One-arm Push-up)
*Date: June 2026*

### What I built

Four new analysis files for the push track — the four exercises whose form is detectable from a standard side camera without any new inverted-pose logic. Three branches of the push tree are now partially or fully analysable. The remaining three skills (Handstand, Handstand Push-up, 90° Handstand Push-up) require inverted-position detection and are deferred.

**`bent_arm_planche.py`:**
Static hold streak, same architecture as `lsit.py` and `straddle_front_lever.py`. Two per-frame criteria: body horizontal (`_compute_body_angle_from_horizontal` from `straddle_front_lever.py`, pass < 25°) AND arms bent (avg elbow < 110°). The upper bound on elbow angle is what distinguishes this from the straddle planche — if the arms straighten it becomes a different skill. Pass: ≥90 consecutive frames (~3s) where both criteria hold simultaneously. Returns `hold_seconds`.

**`straddle_planche.py`:**
The shortest analyser in the project. The straddle planche and straddle front lever are geometrically identical from a side camera — body horizontal + arms straight, with MediaPipe unable to distinguish floor support from bar support. The entire function body is: call `analyse_straddle_front_lever`, set `result["exercise"] = "straddle_planche"`, return. ~10 lines.

**`archer_push_up.py`:**
Same per-side elbow tracking as `archer_pull_up.py`, but the push-up signal is inverted: local MIN = bottom (chest near floor, < 100°), local MAX = top (arms extended, > 150°). The min(left, right) per-frame signal tracks the working arm without advance knowledge of which arm it is. Checks at the bottom frame: working arm < 80° (stricter than push-up's 100° to confirm unilateral loading) and assisting arm > 140°. `_check_pushup_top_extension` is reused at the top frame.

**`one_arm_push_up.py`:**
Imports everything from `push_up.py` and changes only the exercise name. Identical pattern to `one_arm_pull_up.py`.

### What broke / what was hard

Nothing broke. All four exercises mapped cleanly to existing patterns.

### What I learned

**Reuse by calling and renaming vs reuse by importing:**
For straddle_planche, the geometry is completely identical to straddle_front_lever — not just "similar," but literally the same landmark positions. In this case, calling the existing analyser and mutating the exercise key in the return dict is the right pattern. It's honest: the code says "this is the same analysis, different name." The alternative (duplicating the function body) would create two copies of the same logic that could silently diverge. The "call and rename" pattern should be used when the geometry is truly identical; the "import helpers and assemble" pattern (used for one_arm_push_up) is better when the same checks are used but assembled differently.

**Archer push-up checks at the bottom, not the top:**
In the archer pull-up, form is assessed at the top of the rep (peak elbow bend for working arm, peak extension for assisting arm). In the archer push-up, the equivalent moment is the bottom (chest near floor) — that's where the working arm is deepest and the assisting arm is most extended. The top of a push-up is just a plank position; both arms are near straight regardless of archer-style form. Choosing the right frame to evaluate is as important as choosing the right threshold.

**110° as the bent-arm planche threshold:**
The threshold isn't "how bent is bent enough" — it's "how straight is too straight." The bent arm planche fails when the elbows drift toward 180° (becoming a straddle planche), not when they're a few degrees off from ideal. The < 110° check is a ceiling, not a floor. This framing makes it easier to pick a threshold that won't generate false failures.

### Decisions made

**Deferred: Handstand, Handstand Push-up, 90° Handstand Push-up:**
All three require detecting that the person is inverted (wrist_y > hip_y) and knowing MediaPipe landmark reliability is lower for upside-down humans. Implementing them in a separate session keeps each session's scope tight and avoids mixing inverted detection logic with the straightforward exercises above.

**Straddle Planche threshold identical to Straddle Front Lever:**
The 25° from-horizontal threshold was calibrated for the front lever. For the planche, the floor/parallette support means the body may be slightly less horizontal in practice (shoulder depression is harder without bar support), but the 25° tolerance already accommodates this. Using the same threshold keeps the two skills consistent and avoids ad-hoc calibration.

### What's next
- Inverted exercises: Handstand, Handstand Push-up, 90° Handstand Push-up
- Film and upload demo videos for skill nodes

---

## Step 10f — Push track inverted exercises (Handstand, Handstand Push-up, 90° Handstand Push-up)
*Date: June 2026*

### What I built

Three new analysis files and a shared infrastructure change that completes the full push track — all 8 skills are now analysable.

**`pose_service.py` — `flip_vertical` parameter:**
Added `flip_vertical: bool = False` to `extract_landmarks_from_video`. When `True`, every frame is flipped vertically with `cv2.flip(frame, 0)` immediately after `cap.read()`, before the BGR→RGB conversion and MediaPipe processing. `main.py` now defines `INVERTED_EXERCISES = {"handstand", "handstand_push_up", "handstand_push_up_90"}` and passes `flip_vertical=(exercise in INVERTED_EXERCISES)` to the function. All other exercises receive the default `False` — zero behaviour change for everything already working.

**`handstand.py`:**
Static hold streak, same architecture as `lsit.py`. Two per-frame criteria: body alignment (shoulder→hip→knee > 160°, computed inline as `_compute_body_alignment_angles`) and arm lockout (avg elbow > 155°). Per-frame values are AND-ed; the longest consecutive True streak determines `hold_seconds`. Pass: ≥90 frames (~3s). Returns `hold_seconds`. Three cards: `body_alignment`, `arm_lockout`, `hold_duration`.

**`handstand_push_up.py`:**
After the vertical flip, a handstand push-up looks exactly like a pull-up in frame: arms start extended (~170°), flex toward the floor (~90°), then extend back. `_detect_pullup_rep_phases` from `pull_up.py` maps directly — local MAX > 150° is the extended frame (lockout), local MIN < 110° is the flexed frame (head near floor). Reuses `_check_bottom_extension` (elbow > 160° at extended frame) and `_check_top_flexion` (elbow < 90° at flexed frame) unchanged. Three cards: `bottom_extension`, `top_flexion`, `body_alignment`.

**`handstand_push_up_90.py`:**
Identical to `handstand_push_up.py` plus one additional check: `_check_upper_arm_horizontal` verifies `abs(avg_shoulder_y − avg_elbow_y) < 0.05` at the flexed frame. When the upper arm is parallel to the floor, shoulder and elbow sit at the same height. Four cards: `bottom_extension`, `top_flexion`, `upper_arm_horizontal`, `body_alignment`.

### What broke / what was hard

Nothing broke. The vertical flip approach eliminated the need for any custom inverted coordinate logic — after the flip, all existing angle checks and rep-detection code work unchanged.

### What I learned

**Flipping before MediaPipe, not after:**
The initial instinct might be to let MediaPipe run first and then remap the resulting y-coordinates (y → 1 − y). That would fail because MediaPipe's landmark confidence is lower on inverted human poses — the model was trained on upright people. By flipping the raw frame before the model sees it, we give the model its best-case input. The coordinates in the output are already in "upright space" and don't need any remapping. The key insight: fix the input, not the output.

**Why abs(y_shoulder − y_elbow) is preserved under vertical flip:**
Vertical flip maps y → (1 − y). So `y_s_new − y_e_new = (1 − y_s) − (1 − y_e) = y_e − y_s`. The sign flips but `abs(y_s_new − y_e_new) = abs(y_s − y_e)`. This means the upper-arm-horizontal check `abs(shoulder_y − elbow_y) < 0.05` works identically in both flipped and unflipped coordinates — no special handling needed.

**The 90° in "90° Handstand Push-up" is not the elbow angle:**
It refers to the upper arm angle from vertical — when the upper arm is horizontal (90° from vertical), the elbows are level with the shoulders. This is the hardest standard range of motion for the movement. The elbow angle at that point is actually around 90° too, but that's a coincidence — the defining criterion is upper arm position, not elbow angle.

### Decisions made

**`INVERTED_EXERCISES` as a set in `main.py`, not a flag on each analyser:**
The flip is a pre-processing step that happens in `pose_service.py` before any analysis code runs. The analyser functions themselves have no way to request a flip — they only receive the already-processed `landmarks_per_frame`. A set in `main.py` keeps the flip logic centralised: one place to add new inverted exercises, one place to see which exercises need it.

**Inline `_compute_body_alignment_angles` in `handstand.py` (not exported from `_shared.py`):**
The function computes shoulder→hip→knee angles per frame — the same joints used by `_check_body_alignment` in `_shared.py`. I didn't add it to `_shared.py` because it only exists to feed the streak loop in `handstand.py`. If a second static-hold exercise needed per-frame body angles, I'd promote it. Premature export creates API surface for no benefit.

**Reused `_check_bottom_extension` and `_check_top_flexion` despite the naming mismatch:**
Those functions are named for pull-up context ("bottom" = hanging, "top" = chin over bar). In HSPu context, "bottom" maps to the extended/lockout position and "top" maps to the head-near-floor position — inverted semantics. But the check implementations only care about threshold comparisons, not names. Reusing them is correct; the naming mismatch is documented in both analyser docstrings.

### What's next
- Film and upload demo videos for skill nodes

---

## Step 11 — UX: collapsible general filming tips
*Date: June 2026*

### What I built

A collapsible "General filming tips" section in `SkillModal.jsx`, displayed above the exercise-specific filming instructions whenever `skillState !== 'locked'`.

The section covers four things that affect MediaPipe detection quality regardless of exercise:
- **Background** — plain wall or simple outdoor setting; busy backgrounds can confuse pose detection
- **Lighting** — even, shadow-free light; MediaPipe detects landmarks more reliably with good contrast between the person and the background
- **Clothes** — form-fitting and contrasting with the background; baggy clothing obscures elbow, knee, and hip positions
- **Camera** — tripod or stable surface; camera shake introduces noise into joint tracking and can trigger false positives in movement detection

The section is collapsed by default (a single `filmingTipsOpen` boolean state initialised to `false`) and toggled by clicking the header button. A chevron rotates 180° via CSS transition when the section opens. The tips list only renders when the state is `true` — no animation beyond the chevron, intentionally minimal.

### What I learned

**`<button>` for disclosures, not `<div onClick>`:**
A `<div>` with an `onClick` is not keyboard navigable or announced by screen readers as interactive. A `<button>` is keyboard accessible (tab-stops, Enter/Space to activate) and announced as "button" by assistive technology out of the box — no extra attributes needed. The `aria-expanded` attribute then tells screen readers whether the controlled content is currently open or closed. This is the standard ARIA disclosure pattern and costs nothing to implement correctly.

**CSS Modules and the two-class chevron pattern:**
The chevron rotation uses two separate CSS classes (`.chevron` and `.chevronOpen`) rather than an inline style. Both classes share `transition: transform 0.2s ease`; `.chevronOpen` adds `transform: rotate(180deg)`. Switching between classes in JSX (`filmingTipsOpen ? styles.chevronOpen : styles.chevron`) means the transition runs automatically — React just swaps the class, CSS handles the animation. This keeps animation logic entirely in the stylesheet, not in JavaScript.

**Why filming conditions matter as much as form:**
MediaPipe's landmark confidence drops significantly in low-light, high-clutter, or low-contrast conditions — not because the person's form has changed, but because the model can't reliably locate joints. A user who films in good conditions but executes slightly imperfect form will often get more consistent and accurate feedback than a user with perfect form but filmed against a busy background or in dim lighting. These tips are not just practical advice — they directly affect whether the form analysis returns meaningful results.

### Decisions made

**Collapsible in the modal, not a navbar link or separate page:**
The key constraint is *when* a user needs this information: immediately before uploading. A navbar link or separate page would require the user to navigate away, read it, navigate back, and remember it. Placing the section in the modal means it's visible at the exact moment it's relevant. Collapsed by default means users who already know this aren't forced to read it, and the more important exercise-specific instructions (which are exercise-specific and change each time) remain the first thing they see.

**Collapsed by default:**
An expanded default would push the exercise-specific filming instructions and upload button below the fold on smaller screens, increasing the number of scrolls before the user can act. The most important thing in the modal is "what to film and how to upload for this specific skill" — the general tips are useful but subordinate. Collapse-by-default respects that hierarchy.

**General tips in JSX, not in Supabase:**
The exercise-specific filming instructions live in Supabase because they vary per skill. The general tips are the same for every exercise — there is no scenario where the lighting advice changes for a handstand vs a squat. Putting them in the component directly avoids a database query for content that will never change.

---

## Step 12 — Form analysis accuracy fixes + showcase replacement UX
*Date: June 2026*

### What I built

**Form analysis accuracy fixes (4 bugs):**

- **One-arm push-up — 0 reps + wrong angle:** MediaPipe places the elbow slightly off-axis on a side-on view of a vertical arm, collapsing the shoulder-elbow-wrist angle to ~96° even when the arm is fully extended. Smoothing (window=11) made it worse — any brief angle peak was averaged away. Fix: abandon elbow angles for rep detection entirely. Instead use wrist-shoulder vertical distance (`wrist_y − shoulder_y`) — this signal has a large range (~0.3 normalised units) that's unaffected by the elbow placement ambiguity. Rep is detected if `signal_range > 0.02`. Separate per-frame reads at the identified top/bottom frames still use elbow angles (with a lowered 110° pass threshold for extension to account for the known side-on limitation).

- **Squat 500 error ("something went wrong"):** `LANDMARK_NAMES` in `pose_service.py` only included indices 11–26, stopping at the knees. The squat, BSS, and pistol analysers call `_compute_knee_angles` which reads `frame["left_ankle"]` / `frame["right_ankle"]` (indices 27/28). These keys were never populated → `KeyError` at runtime. Fix: add indices 27 (`left_ankle`) and 28 (`right_ankle`) to `LANDMARK_NAMES`. This also unblocked all core analysers which needed ankles.

- **Bulgarian split squat — 0 reps detected:** The original signal was `min(left, right)` per frame. At the top of a BSS, the front knee extends to ~155° but the rear knee stays at ~110° (foot still on the bench). So `min(L,R) ≈ 110°` at the top — never crossing the 150° top threshold → no reps. Fix: dual-signal rep detection. Bottom detection uses `min(L,R)` (working/front knee most bent → reliable minimum). Top detection uses `max(L,R)` (front knee extended → always crosses 150° regardless of rear leg). Same pattern applied to pistol squat.

- **Pistol squat — free leg angle false fail:** At the bottom of a pistol squat, the free knee passes behind the working leg from the side-on camera angle. MediaPipe predicts a plausible but wrong position with medium confidence (~90°), bypassing the visibility gate. Fix: skip any frame where the working knee angle < 100° — this is the occlusion zone. The free leg IS visible during descent, ascent, and standing phases (most of the video), so the check still has plenty of frames to evaluate.

**Skeleton overlay — ankle connections:**
Added `['left_knee', 'left_ankle']` and `['right_knee', 'right_ankle']` to `SKELETON_CONNECTIONS` in `SkillModal.jsx`. The overlay now draws the full lower leg.

**Filming tips additions:**
Added "Trim" and "Rep quality" tips to the collapsible general filming tips section. "Trim" explains to cut the video to just the movement. "Rep quality" warns that only the first detected rep is evaluated, so the first rep should be the best. Added a demo hint below exercise-specific instructions that points to the demo video for form reference (only shown when a demo video exists and the skill is unlockable).

**Showcase replacement UX:**
Previously, passing any attempt silently saved/overwrote the showcase video. Now:
- After any pass (first-time unlock or re-attempt), a prompt appears beneath the feedback cards asking whether to save the video as the showcase.
- First-time unlock: "Save this as your showcase video?" with "Save" / "Skip" buttons.
- Re-attempt: "Replace your showcase with this attempt?" with "Lock it in" (track-coloured) / "Keep current" buttons.
- "Skip" on a first-time unlock still flips the skill to unlocked; the user just has no showcase video stored yet.
- Removed the "Your unlock attempt" heading above the video — the video speaks for itself.
- The "Re-attempt" button on unlocked skills was renamed to "Improve".

**Storage re-upload fix:**
The original approach used `upload(path, file, { upsert: true })` with a fixed path `${userId}/${skillId}.mp4`. Supabase Storage's RLS for the `unlock-videos` bucket grants INSERT to authenticated users but not UPDATE. Upserting an existing file internally issues an UPDATE → silently blocked. Fix: include a timestamp in the path: `${userId}/${skillId}-${Date.now()}.mp4`. Every upload is now always a fresh INSERT. When the user chooses "Lock it in" on a re-attempt, the old file is deleted from storage after the new one is successfully uploaded — the old path is extracted from the stored public URL by splitting on `/unlock-videos/`.

### What broke / what was hard

**Diagnosing the one-arm push-up elbow issue:**
The first attempt used `max(L,R)` elbow angles, expecting that the working arm (more extended at top) would produce a higher angle. But the smoothing window compressed any brief peaks, and the underlying elbow placement problem meant even the raw signal never reached 160°. The fix required stepping back from elbow angles entirely.

**The storage upsert failure was silent:**
Supabase Storage returns an error object but the original code only logged it and returned early. The async function exited before updating `unlockedVideoMap`, so the showcase video appeared unchanged. The user saw no error in the UI. Diagnosis required reasoning about Supabase RLS and INSERT vs UPDATE permissions.

**Race condition between async upload and modal close:**
When the user clicks "Lock it in", `handleShowcaseChoice` fires `onAttemptComplete` (async) without awaiting it, then clears `pendingAttempt`. The async upload takes ~1–2 seconds. If the user closed the modal before the upload finished, `handleClose` would read `pendingUnlockRef.current = null` and skip the video map update. This was discovered as a separate issue from the RLS bug. The storage timestamp fix resolved both problems simultaneously — once uploads succeeded, timing mattered less for the video map update.

### What I learned

**MediaPipe elbow placement on vertical arms from a side camera:**
When a person stands sideways and their arm extends straight up, the elbow is directly between shoulder and wrist in the real world. But MediaPipe may place it slightly laterally (not perfectly in line), collapsing the three-point angle to ~90–100° instead of ~170°. This is a known limitation: the model was trained on diverse poses and the side-on vertical arm is ambiguous. The lesson: elbow angle is reliable for horizontal arm movements (push-ups, pull-ups) but unreliable for vertical arm movements. When the signal doesn't make sense, think about what the landmark estimator is actually seeing.

**Dual-signal rep detection for asymmetric exercises:**
Single-signal detection (`min(L,R)` throughout) assumes the signal that detects the bottom also crosses the threshold for the top. For asymmetric exercises (BSS, pistol squat, one-arm variants), one limb is structurally constrained to a non-neutral position throughout the movement, pulling the average or minimum in a way that prevents top detection. The solution is always: use `min(L,R)` for bottom (most bent = working side drives the minimum) and `max(L,R)` for top (most extended = working side drives the maximum). These two signals are built from the same raw angles but look for different things.

**Supabase Storage RLS: INSERT vs UPDATE are separate operations:**
Supabase Storage policies are defined per HTTP operation — GET, INSERT, UPDATE, DELETE — just like table RLS. A typical "users can upload their own files" policy grants INSERT for paths matching `auth.uid()`. If you upsert (which Supabase internally routes as UPDATE when the file exists), the operation is blocked even though an INSERT would have succeeded. The timestamp-in-path pattern is the standard workaround: every upload is a new object, so it's always an INSERT. Old files are cleaned up explicitly after a successful new upload.

**Deferred commits don't survive race conditions:**
The `pendingUnlockRef` pattern (store the result in a ref, apply it on modal close) is correct for first-time unlocks because the node animation should play after the modal dismisses. But for re-attempts, it introduces a race: the async upload might not finish before the user closes the modal. The pattern to watch for: any `useRef.current = value` that is read in an event handler that can fire before an awaited async operation completes. For re-attempts, the fix would be to update state directly in the async function rather than via the ref — but this became moot once the RLS bug was fixed, since the timestamp path ensures uploads complete quickly.

### Decisions made

**Wrist-shoulder distance over elbow angle for one-arm push-up rep detection:**
The distance signal (`wrist_y − shoulder_y`) is geometrically robust: at the top of a push-up the wrist is far below the shoulder (~0.3 units), at the bottom they're much closer. This is true regardless of elbow placement ambiguity. Using the wrong landmark (elbow) for the wrong signal (angle on a vertical arm) was the root cause of two bugs (0 reps, wrong angle). Switching to the right signal fixed both.

**Showcase prompt deferred to user choice, not automatic:**
Always overwriting on re-attempt was the original behaviour. Always prompting feels more intentional — it respects that the current showcase video might be better than the new one (a good day vs a tired day). For first-time unlocks, the skip option exists because some users might pass a scrappy attempt and want to come back with a cleaner video before committing one to their profile.

**Delete old file after new upload, not before:**
Deleting first and then uploading means a failure during upload leaves the user with no showcase video at all. Uploading first and then deleting means the worst case (deletion fails) is two copies of the video in storage — harmless. Always operate in the order that leaves data in the best state if the second step fails.

### What's next
- Film and upload demo videos for skill nodes

---

## Step 13 — Side-on camera accuracy (visibility-aware joint averaging + threshold fixes)
*Date: June 2026*

### What I built

A targeted set of backend accuracy fixes for the pull and core tracks, addressing two distinct failure modes that both stem from filming side-on.

**Visibility-aware averaging for `_compute_elbow_angles`, `_compute_hip_angles`, `_compute_knee_angles` (`_shared.py`):**

All three functions previously computed `(left_angle + right_angle) / 2` for every frame with no visibility check. From a side-on camera, the far arm/leg is partially occluded. MediaPipe still produces a coordinate for it — often by mirroring the visible side — and keeps its visibility score above 0.5. So the old "skip if visibility < 0.5" guard didn't help: the bad estimate passed the gate with a confident-looking score.

New logic: check all three joints on each side. If both sides have all joints ≥ 0.5 visibility, average them. If only one side clears the threshold, use that side alone. If neither clears it (rare, fallback only), use the raw average to avoid a gap in the signal. This mirrors the pattern already used in `_check_body_alignment`, which was written later and got it right.

**`_check_kipping` (`pull_up.py`) and `_check_no_swing` (`leg_raise.py`):**

Both functions check for excessive frame-to-frame position change (shoulder y for kipping, hip y for swinging). The original threshold was 0.03 — single-frame MediaPipe jitter on a controlled, legitimate rep could easily produce a delta above this, triggering a false fail. Two changes:
1. Apply a 3-frame moving average to the y-signal before computing deltas — this suppresses one-frame spikes without blunting the detection of sustained, fast movement.
2. Raise the threshold from 0.03 to 0.05.

`_check_no_swing` is imported by `toes_to_bar.py` and `one_arm_toes_to_bar.py`, so the fix covers all three exercises.

**`muscle_up.py` above-bar lockout:** the hip y and wrist y values used to verify the lockout position now use only the visible side(s), same pattern as the shared compute functions.

**`toes_to_bar.py` height check:** the ankle and wrist y-values compared at top frames now use visibility-aware averaging.

### What broke / what was hard

**The visibility score is not an occlusion flag:**
The initial assumption was that MediaPipe marks occluded joints with low visibility. It doesn't — it marks them with the confidence of its *estimate*, which may still be above 0.5 even when the estimate is wrong. MediaPipe predicts occluded joints by mirroring from the visible side plus its prior on typical human body configurations. The result is a "confident but wrong" coordinate that passes the old visibility gate and corrupts the average. This meant the bug only showed up when actually testing side-on videos — unit tests with synthetic data wouldn't catch it.

**False kipping fails on clean pull-ups:**
Testing revealed that a controlled, dead-hang pull-up with no momentum was triggering the kipping check. The shoulders move upward throughout the pulling phase — that's just the movement. A 0.03 per-frame delta corresponds to about 22 pixels in a 720p video at 30fps. Normal controlled motion at the top of the pull exceeded this in a single frame. Smoothing the signal first eliminates the jitter spikes; the higher threshold accommodates the genuine speed of controlled movement.

### What I learned

**"Confident but wrong" — why visibility filtering didn't work before:**
MediaPipe's visibility score answers "how confident is the model that it can see this joint?" not "is this joint actually visible from the camera?" A joint that's occluded behind the body can receive a high confidence score if the model predicts a plausible position based on the rest of the skeleton. The correct approach is to think about camera geometry: in a side-on video, exactly one side's joints will be near-facing (accurate) and one side's will be far-facing (estimated). Testing which side has reliably seen joints — rather than relying on confidence alone — is what visibility-aware averaging achieves.

**The importance of testing with real camera angles:**
Every analyser was initially tested with synthetic data or front-facing camera angles where both sides were visible. Side-on camera issues only manifest when filming at 90°. For a calisthenics app where side-on is the *required* filming angle for almost every exercise, this was the most important camera case to get right — and it was the last one tested. Lesson: test with the exact filming conditions the app instructs users to use.

**Smoothing before delta vs smoothing before rep detection:**
The existing smoothing (window=11) is applied to the elbow/knee/hip angle signal for rep detection — it smooths the shape of the wave. The new 3-frame smoothing in `_check_kipping` and `_check_no_swing` is applied to the raw y-coordinate signal before taking frame-to-frame differences. These are different operations: the first smooths for signal shape, the second smooths for rate-of-change. A 3-frame window is intentionally small — it removes single-frame spikes while still detecting a 3+ frame run of fast movement, which is what actual kipping looks like.

### Decisions made

**Fallback to raw average when neither side is visible:**
Rather than skipping a frame entirely when both sides have low-visibility joints, the functions fall back to the raw average. Skipping frames would create gaps in the signal that could corrupt rep detection (the smoothing and local-extrema finding both assume one value per frame). The fallback is honest: "we can't trust either side, so we average and accept some inaccuracy for this frame." This is rare in practice — at least one side is reliably visible in nearly every frame of a side-on video.

**3-frame window for swing/kipping smoothing, not 11:**
Using window=11 (the rep detection window) would suppress genuine fast-motion events — a real kipping hip jerk over 5 frames would be averaged away before the delta check. 3 frames removes single-frame jitter while preserving multi-frame events. The goal is different: rep detection needs a smooth wave shape; swing detection needs to preserve sudden real movement.

**Threshold 0.05, not 0.04 or 0.06:**
0.03 was clearly too strict (false fails on clean reps). 0.05 was chosen based on reasoning about normal controlled velocity: at 30fps, moving the shoulder 3.6% of frame height per frame for 3+ consecutive frames (~108px/s in a 720p video where the person fills 60% of frame height) is the kind of sustained acceleration that indicates momentum use. 0.05 is strict enough to catch real kipping; 0.06 started feeling too lenient in review.

### What's next
- Film and upload demo videos for skill nodes

---

## Step 14 — Demo recording calibration: analysis threshold fixes + unlock animation
*Date: June 2026*

### What happened

First session filming real unlock videos in my home gym — a free-standing rack where the uprights sit behind the bar from a side-on angle, plus indoor lighting rather than an open background. Several analysers that passed synthetic tests had calibration issues on real footage. Most failures fell into two categories: **wrong signal** (using the wrong landmark or statistic) and **thresholds calibrated for ideal conditions**.

---

**`_check_kipping` rewrite (pull_up.py):**

Step 13 added 3-frame smoothing and raised the threshold from 0.03 to 0.05, but still used shoulder y and checked the *maximum* delta. Both were wrong:

- Shoulders move upward continuously throughout a pull-up — that's the movement itself. What oscillates during kipping is the **hip** — the hip jerk forward and back generates the momentum. Shoulder y on a strict rep was triggering false fails.
- `max()` fails on a single outlier frame (e.g. jumping to grab the bar at the start of the video).

Fix: track hip y, compute the **95th-percentile delta** from the sorted list of per-frame deltas, pass if p95 < 0.05. Genuine kipping produces many large-delta frames so p95 still catches it; a single noisy frame no longer fails the whole check.

**`_check_no_swing` (leg_raise.py) — same p95 fix:**

This function (imported by toes_to_bar.py and one_arm_toes_to_bar.py) already tracked hip y correctly but also used `max()`. Applied the same p95 pattern.

**`_detect_pullup_rep_phases` — parametrized `window`:**

A 1-second explosive pull-up video (~30 frames) with window=11 puts 37% of the signal inside the smoothing kernel — any brief angle peak gets averaged away and no local extrema are found. Added `window: int = 11` parameter so `explosive_pull_up.py` can pass `window=5`.

**`explosive_pull_up.py` — chest-to-bar tolerance:**

The chest-to-bar check compares average wrist y to average shoulder y. MediaPipe places the wrist landmark at the wrist *bone*, not the fingertips — on a bar grip it sits slightly above the bar. Changed the threshold from `avg_gap >= 0` to `avg_gap >= -0.05`.

**`muscle_up.py` — temporal sequence lockout:**

The above-bar lockout originally compared hip y to wrist y (hips should be above bar = above wrist level). This failed regardless of tolerance because the wrist landmark on a bar grip sits at the back of the wrist, not at bar level — the exact offset depends on grip style and wrist flexion. No positional threshold could reliably solve this.

Fix: abandon positional comparison. Use a **temporal sequence**: find the frame with the deepest pull (minimum elbow angle), then scan everything after that frame for any frame where elbow angle > 150°. If the elbows get deep then fully extend, a lockout occurred — no landmark-position assumption required. Also added `rep_count` to the return dict (was always hardcoded 0).

**`lsit.py` — two-tier threshold calibration:**

All three check cards showed green (averages passing) but the hold duration was always under a second. The mismatch: averages smooth across many frames and suppress noise; the per-frame streak runs on raw landmark values which are much noisier frame-to-frame. The streak condition needs to be noticeably looser than the check-function thresholds.

Changes:
- Average hip angle: `< 100°` → `< 120°` (ankle droop inflates the shoulder-hip-ankle reading)
- Average elbow: `> 155°` → `> 140°` (forward lean for counterbalance makes full lockout impossible)
- Per-frame streak: `h < 100 and k > 155 and e > 155` → `h < 130 and k > 150 and e > 130`

**Parametrized shared functions:**

`_check_leg_straightness`, `_check_body_alignment`, `_check_bottom_extension` all received a `threshold: int` parameter with the existing value as the default. Existing call sites unchanged; callers needing different thresholds pass explicit values.

- `toes_to_bar.py` + `one_arm_toes_to_bar.py`: `_check_leg_straightness(threshold=125)` — hamstrings maximally stretched at full toes-to-bar, some natural knee bend unavoidable
- `one_arm_pull_up.py`: `_check_bottom_extension(threshold=155)` (single arm reads slightly compressed from side camera) + `_check_body_alignment(threshold=145)` (body rotation toward gripping arm reads as hip sag from side camera)

---

**Frontend: unlock animation fixes:**

Two bugs in the showcase-save flow:

1. **Modal close without choosing → skill not unlocked.** If the user dismissed the modal without tapping Save or Skip, `handleShowcaseChoice` was never called and the skill stayed in limbo. Fix: `handleClose` wrapper in `SkillModal.jsx` calls `handleShowcaseChoice(false)` (implicit skip) before `onClose()` whenever `pendingAttempt` exists.

2. **Unlock animation not firing after implicit skip.** `TrackPage`'s `pendingUnlockRef` was set inside the skip path *after* an `await` call. `onClose` fired synchronously — before the `await` resolved — and read `pendingUnlockRef.current === null`. Fix: moved `pendingUnlockRef.current = { skillId, videoUrl: null }` to before the first `await`. JavaScript functions run synchronously until their first `await`, so setting the ref before yielding guarantees the synchronous caller sees it.

### What I learned

**Positional landmark checks are fragile near equipment:**

When a joint is in contact with an object (wrist gripping a bar, foot on a bench), MediaPipe's landmark estimate is offset from the actual contact point by the object's geometry. Temporal sequence checks — "event A happened before event B in the signal" — avoid this entirely. They ask a question about signal shape over time, not about absolute landmark position at a frame.

**Two-tier threshold design for static holds:**

Whenever you run an "average across all frames" check and a "per-frame" check on the same signal, the per-frame threshold must be noticeably looser. Averages suppress noise by construction. If you set both thresholds equal, a single jitter frame that reads just outside the average threshold will break the streak even though the user's hold was genuinely good. A rough rule: start the per-frame threshold 10–20° looser and tighten from there.

**p95 for sustained-movement detection:**

`max()` of frame-to-frame deltas fails on a single outlier frame. The 95th percentile asks "was there *sustained* large movement?" — it ignores the noisiest 5% of frames while still failing on genuine kipping (which produces many consecutive high-delta frames). The pattern: sort deltas, take `deltas[int(len * 0.95)]`.

**Smoothing window vs video length:**

At 30fps, window=11 covers 0.37 seconds. On a 30-frame video (1 second), that's 37% of the signal inside the kernel — peaks flatten and rep detection fails. Parametrize smoothing window when the video length varies significantly between callers.

### Decisions made

**Temporal sequence for muscle-up lockout:**

Positional checks kept failing regardless of tolerance. Switching to "deepest pull then arm extension" encodes the same knowledge a coach has — "did they pull deep and then lock out?" — without any assumption about where the bar is in the frame.

**Per-frame streak thresholds 10–30° looser than average thresholds:**

L-sit: average hip `< 120°` vs streak gate `< 130°`; average elbow `> 140°` vs streak gate `> 130°`. The gaps absorb frame-level noise without relaxing the quality standard as assessed by the diagnostic cards.

### What's next

- Finish filming and uploading demo videos for all skill nodes

---

## Step 15 — Reflection
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


