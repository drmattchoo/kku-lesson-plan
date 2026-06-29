# M11 — Hardening + deploy

## What's hardened (built by Claude Code)
- **Retry-once on bad LLM JSON**: `app/retry.py`'s `call_with_retry` wraps both
  `extraction_service.extract_course` and `outline_service.generate_outline` — one
  retry on malformed/non-matching JSON before giving up.
- **Validation surfaced cleanly**: if a retry still fails, `/api/extract` and
  `/api/outline` return a `502` with a plain Thai message instead of a raw `500`.
  Pydantic's own `422` (e.g. a malformed `PUT /api/course/{sid}` body) is already
  FastAPI's default behavior — no extra wiring needed there.
- **Session persistence**: disk-backed JSON under `sessions/` (gitignored), one file
  per session, keyed by a `uuid4` hex id — built in M6.
- **Rate limiting**: in-process sliding-window limiter (`app/rate_limit.py`) on the
  two LLM-calling endpoints — 5 calls/min for `/api/extract`, 10 calls/min for
  `/api/outline`, keyed per logged-in user. Matches the project's "no real DB needed"
  single-instance scope; if you outgrow a single instance, replace with a Redis-backed
  limiter, but that's not needed for one department's worth of instructors.
- **Single-process deployment**: `app/main.py` mounts the built React app
  (`frontend/dist/`, after `npm run build`) as static files on the same FastAPI
  process that serves `/api/*` and `/auth/*` — one process, one port, no separate
  static host needed. Falls back to nothing (404 on `/`) if `dist/` doesn't exist,
  which is fine in dev (Vite's own dev server + proxy handles the frontend there) and
  in the test suite.
- **`Dockerfile`** at the repo root: multi-stage build (Node stage builds the
  frontend, Python stage runs it). Builds and runs locally — see below.

## What's NOT done here — these are yours
Per the project's own handoff plan (`project-handoff.html`), actually going live is
explicitly **your** step, not Claude Code's:

> "Deploy ask IT — A managed host (Render / Railway / Fly.io) is the easy path — or
> hand it to KKU IT if they want it on university infrastructure."

Nothing in this build has provisioned a host, registered a domain, or pushed a
container anywhere — that requires accounts/credentials only you hold, and is a
real-world infrastructure action outside what an assistant should do unprompted.

### To run it yourself (any of these)

**A. Local Docker (verify the container before picking a host):**
```bash
cd "webapp kk2"
docker build -t lesson-plan-app .
docker run -p 8000:8000 \
  -e GOOGLE_CLIENT_ID=... -e GOOGLE_CLIENT_SECRET=... \
  -e ALLOWED_EMAIL_DOMAIN=kku.ac.th \
  -e LLM_API_KEY=... -e LLM_PROVIDER=claude \
  -e SESSION_SECRET=$(openssl rand -hex 32) \
  lesson-plan-app
```
Real env vars always win over anything in a mounted `.env` (pydantic-settings reads
process env first) — so for production, prefer your host's secret manager over baking
or mounting an `.env` file at all.

**B. Render / Railway / Fly.io**: point them at this repo's `Dockerfile` directly —
all three support "deploy from Dockerfile" with environment variables set in their
dashboard. Set the same env vars as above. Health check path: `GET /health`.

**C. Hand to KKU IT**: give them this repo + this doc. They'll want to know:
- It's a single container, port 8000, health check at `/health`.
- Needs the env vars listed above (their own Google Workspace OAuth app if KKU IT
  wants it on the "Internal" consent-screen tier instead of the current "External" one
  — see `docs/M2-kku-login-setup.md`).
- `sessions/` is local disk state per the container — if they run multiple replicas
  behind a load balancer without session affinity, an instructor's session could
  bounce between replicas and "lose" their in-progress draft. Fine for one container;
  flag it if they want to scale beyond that (swap for SQLite on a shared volume, or a
  real DB — not built here since the project's own scope says "no real DB needed").

## Update PROGRESS.md after you deploy
Once it's live somewhere, note the URL and host in `PROGRESS.md`'s "Decisions made"
section — that's the kind of fact future Claude Code sessions need and can't derive
from the code.
