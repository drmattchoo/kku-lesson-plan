# Staging deploy on Render — do-it-now runbook

Goal: a throwaway staging instance to surface what breaks before the real launch.
Not production — no uptime promise, no real students using it. `docs/M11-deploy.md`
covers the general options (Render/Railway/Fly/KKU IT); this picks **Render**
specifically, the simplest single-container path.

Everything below is **yours to click through** — host signup, creating the service,
adding the OAuth redirect URI in Google's console, and the real-login smoke test.
This doc just tells you exactly what to type where.

## 0. Prerequisite: push this repo to GitHub
Render deploys from a Git provider (GitHub/GitLab) — this repo has no remote yet
(`git remote -v` is empty). Create a new repo on GitHub (private is fine — `.env` is
already gitignored, so no secrets go up) and push:
```bash
cd "webapp kk2"
git remote add origin git@github.com:<you>/<repo-name>.git
git push -u origin main
```

## 1. Pick the service name BEFORE creating it
Render's URL shape is `https://<service-name>.onrender.com`, and you choose
`<service-name>` at creation time — pick it first so you know `BASE_URL` and the
Google callback URL in advance, instead of deploying once just to learn the URL.

Example used below: **`lesson-plan-staging`** → `https://lesson-plan-staging.onrender.com`.
Substitute your actual chosen name everywhere below.

## 2. Create the Render Web Service
1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**.
2. Connect the GitHub repo from step 0.
3. **Name**: `lesson-plan-staging` (or your choice — this fixes the URL).
4. **Root Directory**: leave blank (the `Dockerfile` is at the repo root).
5. **Runtime**: Render should auto-detect "Docker" from the `Dockerfile`. If it
   offers a runtime picker, choose Docker explicitly.
6. **Instance Type**: Free or Starter — this is throwaway staging, the cheapest
   tier that doesn't sleep mid-demo is fine.
7. **Health Check Path**: `/health`.
8. Don't click "Create Web Service" yet — add the env vars first (step 3), since
   Render will trigger a build immediately on creation.

## 3. Environment variables (Render dashboard → Environment)

Copy these from your local `.env` as-is:

| Key | Value source |
|---|---|
| `GOOGLE_CLIENT_ID` | from `.env` |
| `GOOGLE_CLIENT_SECRET` | from `.env` |
| `ALLOWED_EMAIL_DOMAIN` | from `.env` (`kku.ac.th`) |
| `LLM_BASE_URL` | from `.env` (`https://gen.ai.kku.ac.th/api/v1`) |
| `LLM_API_KEY` | from `.env` |
| `LLM_PROVIDER` | from `.env` (`claude`) |
| `LLM_MODEL_CLAUDE` | from `.env` (`claude-sonnet-4.6`) |
| `LLM_MODEL_GPT` | from `.env` (`gpt-5.5`) |

**New for staging — do NOT reuse the local `.env` values for these:**

| Key | Value |
|---|---|
| `SESSION_SECRET` | a FRESH random value — generate with `openssl rand -hex 32`. The local `.env` has the literal placeholder `change-me-dev-only`; never put that on a real host. |
| `BASE_URL` | `https://lesson-plan-staging.onrender.com` (your actual service name, no trailing slash) |
| `SESSION_HTTPS_ONLY` | `true` |
| `ALLOWED_HOSTS` | `lesson-plan-staging.onrender.com` (no scheme, no trailing slash) |
| `CORS_ORIGINS` | leave unset — frontend is same-origin, no CORS needed |

`PORT` is injected automatically by Render — don't set it yourself, the
`Dockerfile`'s `CMD` already reads `$PORT` if present.

Now click **Create Web Service**. First build takes a few minutes (it's compiling
the frontend in the Node stage, then installing Python deps).

## 4. Add the callback URL to the Google OAuth client
[console.cloud.google.com](https://console.cloud.google.com) → your OAuth client
(the one whose ID/secret are in `.env`) → **Authorized redirect URIs** → add:
```
https://lesson-plan-staging.onrender.com/auth/callback
```
(your actual service name). Keep the existing `http://localhost:8000/auth/callback`
entry too — that's still used for local dev.

## 5. Smoke test (once Render shows "Live")
1. Open `https://lesson-plan-staging.onrender.com` — the instructor-form Stage 1
   wizard page should load (not a 404, not a blank page).
2. Click through to sign in with your real `@kku.ac.th` Google account — confirm it
   redirects to the real Google consent screen and back without an OAuth error
   (mismatched redirect URI is the single most likely failure here — if Google
   complains "redirect_uri_mismatch", re-check step 4 matches `BASE_URL` exactly,
   including `https://` and no trailing slash).
3. Upload one real มคอ-3 spec (e.g. `tests/fixtures/DT.docx` or one of your own) and
   confirm the extracted draft shows up on the correction screen.
4. Pick a lecture, generate + save an outline, then export it.
5. Open the downloaded `.docx` in Word — confirm it looks like a real KKU lesson plan
   (header fields filled, PLO/CLO list, the timed table, no `CLOCLO1`-style
   double-prefixed ids, no blank content cells).

If any step fails, check Render's **Logs** tab first — `_run_llm_step`'s 502s and any
`enforce_rate_limit` 429s will show there with a clear message.

## What this staging deploy does NOT cover
- Multiple replicas / autoscaling — `sessions/` is local container disk; a second
  replica wouldn't see a session created on the first one. Fine for one instance.
- A custom domain — Render's `.onrender.com` URL is enough for staging; if you want
  a real domain later, that's a separate Render dashboard step (and a `BASE_URL` /
  `ALLOWED_HOSTS` / Google-console update to match).
- This is explicitly **not** production hardening beyond what M11 already built
  (retry-once, rate limiting, 502 surfacing) — it's meant to surface bugs cheaply,
  not to be the final home for real student data.

## After this works
Note the live URL and anything that broke in `PROGRESS.md`'s "Decisions made" section
— what staging surfaces here is exactly the kind of fact a future session can't
derive from the code alone.
