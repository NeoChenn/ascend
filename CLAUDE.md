# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Calisthenics Coach

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

An AI-powered calisthenics coaching web app. Users upload a video of themselves performing a calisthenics skill, receive automated form feedback based on pose estimation, and track their progression through a visual skill tree.

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
| LLM feedback (stretch) | Claude API |

## Project structure (planned)

```
calisthenics-coach/
├── frontend/          # React + Vite app
│   ├── src/
│   │   ├── pages/     # Home, Upload, SkillTree
│   │   ├── components/
│   │   └── App.jsx
├── backend/           # FastAPI app
│   ├── main.py
│   ├── routes/
│   ├── services/      # Pose estimation logic, form analysis
│   └── models/        # Data models
└── CLAUDE.md
```

## MVP features

1. **Video upload + pose extraction** — user uploads a video, backend runs MediaPipe and returns joint coordinates
2. **Form feedback** — angle-based analysis for pull-ups and push-ups, returning structured feedback
3. **Skill tree** — visual progression map, user can mark skills as in-progress or completed
4. **User accounts** — Supabase auth, save upload history and skill progress

## Out of scope for MVP

- Real-time webcam analysis
- Mobile app
- Social features
- More than 2-3 exercises

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

