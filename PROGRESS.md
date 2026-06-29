# Build progress

Read this first each session, then run the test suite. Update it as the LAST act
of every session.

## Status
**ALL MODULES BUILT (M0-M11).** Tree state: ☑ green (67 backend tests, frontend
build+lint clean). Last green commit: b70e7b9 — "M11: single-process deploy (serve
built frontend from FastAPI), Dockerfile, deploy doc — actual hosting decision left
to user per project plan ✓"

A full end-to-end live run (real DT.docx extraction → instructor correction → real
outline generation with a brief → manual edit → single export → second outline →
batch export to .zip) passed cleanly with NO mocking anywhere in the chain except
auth (Google login can't be scripted without real credentials). See "Decisions made"
below for what's still genuinely outstanding (deployment itself, a few UX rough
edges) vs. what's done.

## Your homework (do before opening Claude Code) — all done
- [x] One clean official KKU lesson-plan .docx + written list of every field it needs
- [x] Google sign-in credentials (Google Cloud, restricted to kku.ac.th) — in .env
- [x] University API key + chosen model — KKU gateway (gen.ai.kku.ac.th) key in .env,
      verified live against both claude-sonnet-4.6 and gpt-5.5
- [x] 2–3 REAL messy course specs to test extraction against — DT.docx (user-confirmed
      current real spec) + PT.docx, both extracted live, GATE passed

## Modules
| Phase | Module | Built | Tested | Notes |
|-------|--------|-------|--------|-------|
| 0 | M0  scaffold + config            | ☑ | ☑ | /health returns active model |
| 0 | M1  template binder + render proof [reuse] | ☑ | ☑ | GATE passed: human verified render_proof.docx vs KKU standard |
| 1 | M2  Google sign-in (@kku.ac.th)  | ☑ | ☑ | Authlib + Starlette SessionMiddleware; every /api/* guarded |
| 2 | M3  LLM provider interface       | ☑ | ☑ | single OpenAI-SDK client against KKU gateway, model-switched |
| 2 | M4  document loaders [reuse]     | ☑ | ☑ | tested against real curriculum/ docx + real pptx |
| 2 | M5  extraction service [reuse]   | ☑ | ☑ | GATE passed on real DT.docx + PT.docx — see backend/extraction_proof/*.json |
| 3 | M6  instructor form              | ☑ | ☑ | React+Vite wizard Stage 1; live-verified in real Chrome incl. real Google redirect |
| 3 | M7  upload + correction screen   | ☑ | ☑ | POST /api/extract, GET/PUT /api/course/{sid}; editable PLO/CLO/lecture lists + picker |
| 3 | M8  outline service              | ☑ | ☑ | all 3 grounding modes live-verified — see backend/outline_proof/*.json |
| 3 | M9  outline editor               | ☑ | ☑ | POST/PUT /api/outline wired; edit/reorder/add/remove key points, live total |
| 3 | M10 batch export                 | ☑ | ☑ | POST /api/export(/batch); lesson_plan_assembler maps session->render context |
| 4 | M11 hardening + deploy           | ☑ | ☑ | retry-once, 502 surfacing, rate limit, single-process static serving, Dockerfile |

## Decisions made
- Auth: Google only, @kku.ac.th allowlist (confirmed by user). No payment.
- Template key-point table is a real Word table → docxtpl loops over rows using the
  {%tr for/endfor%} convention, each tag alone in its own row (open-tag row, body row,
  close-tag row) — putting both tags in the same row breaks docxtpl's regex.
- Multi-line table cells (เนื้อหา) need docxtpl's `{{r ... }}` RichText run-tag, not
  plain `{{ }}` — and that field must ALWAYS be converted to RichText regardless of
  whether it contains a newline, because the `{{r}}` tag always strips the enclosing
  `<w:r>` at the XML level. A plain string with no `\n` rendered as a BLANK cell before
  this was fixed (found via the M10 real-data pipeline check, not by the unit tests,
  since the M1 dummy fixture happened to always have multi-line content).
- วัตถุประสงค์ is a CLO-tied action statement per key point, never a copy of the title.
- ผลการเรียนรู้ column (table) AND the PLO/CLO heading list (paragraphs) both
  normalize ids before rendering — real LLM extraction sometimes returns ids already
  prefixed ("CLO1") instead of bare ("1"), and naively prepending "CLO"/"PLO" again
  produced "CLOCLO1"/"PLOPLO4". `template_binder._strip_prefix` fixes both the table
  (`_format_lo_refs`) and the heading list (`_prepare_context`'s PLOs/CLOs id
  normalization) — found via the M10 real-data pipeline check.
- Google OAuth client registered with explicit authorize/token URLs (no discovery-doc
  fetch) so /auth/login needs no network access and is fully unit-testable offline.
- LLM is NOT two separate provider SDKs — gen.ai.kku.ac.th is one OpenAI-compatible
  gateway that routes to Claude/GPT/others by `model` name. app/llm.py is a single
  `openai` SDK client pointed at that base_url; "switch by config" just changes the
  model string (LLM_PROVIDER=claude|gpt in .env), not the client class. **Per-key
  daily quota is shared across models** — hit "daily limit" on claude-sonnet-4.6
  mid-build from cumulative testing; switching `LLM_PROVIDER=gpt` worked immediately
  as a fallback. Worth knowing if live testing/usage hits a wall.
- docx loader walks the body in document order (paragraphs interleaved with tables) —
  มคอ tables are meaningless out of context. Horizontally-merged table cells repeat
  the same text N times in `row.cells` (python-docx quirk) → deduped per row.
  PDF (PS.pdf) is explicitly NOT supported by M4 — out of CLAUDE.md's documented
  scope (pptx/docx only); flag if a real มคอ shows up as PDF.
- Real มคอ-3 specs legitimately have NO PLOs (DT.docx's PLO/CLO mapping table is
  headers-only with empty rows — only applies to thesis-type courses). Extraction
  must return PLOs: [] in that case, never invent PLOs to fill the gap.
- Schedule tables almost never state CLO ids per row directly — the extraction prompt
  has the LLM infer cloRefs by matching topic text against extracted CLOs. Best-effort;
  the instructor corrects via M7, not M5's job to be perfect.
- session_store is disk-backed JSON under repo-root sessions/ (gitignored), keyed by a
  uuid4 hex id; tests monkeypatch session_store.SESSIONS_DIR to tmp_path for isolation.
- InstructorProfile needed a `learners` field (the KKU template's "ผู้เรียน" target-
  audience line) that nothing originally captured — added during M10 when building
  the render-context assembler exposed the gap. sessionDate/sessionTime are NOT part
  of any earlier-stage schema; they're collected at export time (M10's UI) since
  they're naturally tied to "when are you actually teaching this", which can vary by
  section/group even for the same generated outline.
- The KKU template only shows the date/time block on the table's FIRST row, blank for
  the rest — confirmed against both real filled examples (PT_ANS_2569.docx,
  PS_ANS_2569.docx) — `lesson_plan_assembler.build_render_context` sets timeLabel only
  on keyPoints[0], no per-row time-arithmetic.
- Node.js/npm IS installed on this machine via nvm (`~/.nvm`, node v24.18.0, npm
  11.16.0) — just not on PATH by default in a fresh shell. Always run
  `export NVM_DIR="$HOME/.nvm"; source "$NVM_DIR/nvm.sh"` before any node/npm command.
- frontend/ is a Vite+React scaffold; dev proxy in vite.config.js forwards /api and
  /auth to localhost:8000 for local dev (vite on 5173, uvicorn on 8000). In
  production, `app/main.py` mounts `frontend/dist/` (after `npm run build`) as static
  files on the SAME FastAPI process — one container, one port. See `docs/M11-deploy.md`.
- Browser verification used the Claude-in-Chrome MCP, not the Preview MCP —
  preview_start needs `.claude/launch.json` relative to the session's registered
  project root (webapp_kk1), but this app's code lives in the sibling dir `webapp kk2`.
  Did NOT attempt actual Google login in the browser (needs real credentials, a
  prohibited action) — confirmed the redirect URL/params are correct via real Chrome,
  and verified every authenticated flow via TestClient with a mocked Google token
  (which exercises the real session-cookie code path, just not a literal browser).
- LLM-calling endpoints (`/api/extract`, `/api/outline`) are rate-limited per user
  (5/min, 10/min respectively) via an in-process sliding window — matches "no real DB
  needed" scope; would need a shared store (Redis) only if scaled beyond one instance.
- Persistent (post-retry) LLM failures surface as a clean `502` with a Thai message,
  not a raw `500` — `app/main.py`'s `_run_llm_step` helper.
- Actual deployment (picking a host, DNS, going live) was deliberately NOT done —
  that's the user's own step per the project's own handoff plan (project-handoff.html
  literally says "Deploy ask IT"). Built: Dockerfile, single-process static serving,
  and `docs/M11-deploy.md` explaining exactly how to run it on Render/Railway/Fly.io
  or hand to KKU IT. Docker itself isn't installed on this machine, so the Dockerfile
  is carefully path-checked against the real repo structure but NOT build-tested.

## Open questions / blockers
- None blocking further backend/frontend work. Real-world gaps worth the user's
  attention before going live:
  - The Google Cloud OAuth consent screen is presumably "External" mode (since
    "Internal" needs the Cloud project inside KKU's Workspace org) — confirm with KKU
    IT per `docs/M2-kku-login-setup.md` step 0 if they want the stricter tier.
  - `sessions/` is local disk — fine for one container; flag to KKU IT if they want
    multiple replicas without session affinity (see `docs/M11-deploy.md`).
  - References (course textbook list) are never extracted or rendered — out of scope
    by design (M5's ExtractedCourse schema has no references field); the KKU template's
    References section will always render empty unless this is added later.

## Next session should start by
- Nothing is blocking. If picking this up again: either (a) deploy it somewhere per
  `docs/M11-deploy.md` and report back the URL/host so this file can be updated, or
  (b) do a real end-to-end click-through in a browser with YOUR actual KKU Google
  account (something I structurally cannot do), to catch anything the mocked-auth
  test suite can't — e.g. the real OAuth consent screen experience, real cookie
  behavior across the 5-stage wizard, or any UI rough edges on the correction/outline
  screens that only show up with real extracted data of your choosing.
