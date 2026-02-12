# AI-Powered Online Classroom Engagement & Performance Analytics Platform

This repository contains a working backend foundation for **Phase 0 → Phase 6** and frontend mockups for the early dashboard/meeting UX.

## Implemented phases

### Phase 0 (Core backend foundation)

- Authentication: register/login
- Role model: `admin`, `teacher`, `student`
- Admin-protected setup APIs:
  - departments
  - academic years
  - sections
  - subjects
- Assignment APIs:
  - teacher → subject
  - student enrollment (department + section + academic year)

### Phase 1 (Dashboard mock data APIs + UI mockups)

- Dummy dashboard API endpoints:
  - `GET /dashboards/student/{student_id}`
  - `GET /dashboards/teacher/{teacher_id}`
  - `GET /dashboards/admin/overview`
- Static dashboard mock UI:
  - `frontend/phase1-dashboards.html`

### Phase 2 (Basic meeting workflow APIs + UI mockup)

- In-memory meeting/session APIs:
  - `POST /meetings`
  - `POST /meetings/{meeting_id}/join`
  - `POST /meetings/{meeting_id}/leave`
  - `POST /meetings/{meeting_id}/end`
  - `GET /meetings/{meeting_id}/participants`
  - `POST /meetings/{meeting_id}/chat`
  - `GET /meetings/{meeting_id}/chat`
- Constraints:
  - max 2 concurrent participants (for pilot scope)
  - attendance captured when participant joins
- Static meeting UI mock:
  - `frontend/phase2-meeting.html`

### Phase 3 (Caption pipeline)

- Teacher/admin can push time-bounded caption segments:
  - `POST /meetings/{meeting_id}/captions`
- Authenticated users can list collected captions:
  - `GET /meetings/{meeting_id}/captions`
- Host/admin can finalize caption transcript:
  - `POST /meetings/{meeting_id}/captions/finalize`
- Captions are stored in database table `caption_segments` with fields:
  - meeting id
  - teacher id
  - start/end second
  - text


### Phase 4 (Quiz generation + review + submission)

- Generate quiz from finalized caption transcript context:
  - `POST /meetings/{meeting_id}/quizzes/generate`
- Teacher/admin can review and edit generated questions:
  - `GET /quizzes/{quiz_id}`
  - `GET /quizzes/{quiz_id}/questions`
  - `PUT /quizzes/{quiz_id}/questions/{question_id}`
- Teacher/admin can publish quiz:
  - `POST /quizzes/{quiz_id}/publish`
- Student can submit answers and receive score:
  - `POST /quizzes/{quiz_id}/submit`

- Persisted tables added:
  - `quizzes`
  - `quiz_questions`
  - `quiz_submissions`


### Phase 5 (Engagement analytics pipeline)

- Host teacher/admin can record sampled engagement scores for students in a meeting:
  - `POST /meetings/{meeting_id}/engagement-samples`
- Authenticated users can view meeting-level engagement summary:
  - `GET /meetings/{meeting_id}/engagement-summary`
- Student (self), teacher, or admin can view overall student engagement profile:
  - `GET /students/{student_id}/engagement/overall`

- Persisted table added:
  - `engagement_samples`


### Phase 6 (Performance analytics scoring)

- Student performance analytics endpoint (quiz + engagement composite):
  - `GET /analytics/students/{student_id}/performance`
- Teacher performance analytics endpoint (published quiz outcomes + engagement trends):
  - `GET /analytics/teachers/{teacher_id}/performance`
- Admin institution analytics endpoint (institution-level score and totals):
  - `GET /analytics/admin/institution`

## Tech stack

- FastAPI
- SQLAlchemy
- SQLite
- JWT auth (`python-jose`)
- Password hashing (`passlib[bcrypt]`)
- Pytest

## Project structure

- `app/main.py` – API routes (Phase 0/1/2/3/4/5/6)
- `app/models.py` – SQLAlchemy models
- `app/auth.py` – JWT + role guard utilities
- `app/database.py` – database setup/session
- `app/schemas.py` – request/response schemas
- `frontend/` – Phase 1/2 HTML prototypes
- `tests/` – integration-style API tests by phase

## Run locally

### 1) Install dependencies

```bash
pip install -e .[dev]
```

### 2) Start API server

```bash
uvicorn app.main:app --reload
```

### 3) Open API docs

- Swagger: `http://127.0.0.1:8000/docs`

## Next phases

- Production hardening: replace in-memory meeting state with persistent/realtime infrastructure, add async job queues for inference, and add privacy-governed model operations.
