# Build progress

Read this first each session, then run the test suite. Update it as the LAST act
of every session.

## Status
Current session target: Phase 0-2 complete, Phase 3 in progress (M0-M6, M8)
Last green commit: e0dce47 — "M6: instructor form (Stage 1) — React+Vite wizard shell, POST /api/session, live-verified in browser ✓"
Tree state: ☑ green

## Your homework (do before opening Claude Code)
- [x] One clean official KKU lesson-plan .docx + written list of every field it needs
- [x] Google sign-in credentials (Google Cloud, restricted to kku.ac.th) — in .env
- [x] University API key + chosen model — KKU gateway (gen.ai.kku.ac.th) key in .env,
      verified live against both claude-sonnet-4.6 and gpt-5.5
- [x] 2–3 REAL messy course specs to test extraction against — DT.docx (user-confirmed
      current real spec) + PT.docx, both extracted live, GATE passed (see below)

## Modules
| Phase | Module | Built | Tested | Notes |
|-------|--------|-------|--------|-------|
| 0 | M0  scaffold + config            | ☑ | ☑ | /health returns active model |
| 0 | M1  template binder + render proof [reuse] | ☑ | ☑ | GATE passed: human verified render_proof.docx vs KKU standard; objective/content tied to CLOs, ผลการเรียนรู้ column computed as PLO/CLO pairs |
| 1 | M2  Google sign-in (@kku.ac.th)  | ☑ | ☑ | Authlib + Starlette SessionMiddleware; /api/* guarded via require_kku_user; tests mock Google token, no network in test suite |
| 2 | M3  LLM provider interface       | ☑ | ☑ | app/llm.py — single OpenAI-SDK client against KKU gateway, model-switched; live-verified against claude-sonnet-4.6 + gpt-5.5 |
| 2 | M4  document loaders [reuse]     | ☑ | ☑ | app/document_loaders.py; tested against real curriculum/ docx + the real pptx, not synthetic fixtures |
| 2 | M5  extraction service [reuse]   | ☑ | ☑ | app/extraction_service.py + app/schemas.py; GATE passed on real DT.docx (55 lectures, 4 CLOs, correctly 0 PLOs) and PT.docx (33 lectures, 3 CLOs) — see backend/extraction_proof/*.json |
| 3 | M6  instructor form              | ☑ | ☑ | frontend/ scaffolded (React+Vite, Node found via nvm); Stage-1 form live-verified in real Chrome — filled all 10 fields, submitted, correctly redirected to the real Google consent screen with hd=kku.ac.th |
| 3 | M7  upload + correction screen   | ☐ | ☐ | the load-bearing gate for messy input |
| 3 | M8  outline service              | ☑ | ☑ | app/outline_service.py; live-verified all 3 grounding modes against real DT.docx lectures (spec-alone + slides-grounded), durations sum exactly — see backend/outline_proof/*.json |
| 3 | M9  outline editor               | ☐ | ☐ | |
| 3 | M10 batch export                 | ☐ | ☐ | reuses M1 binder |
| 4 | M11 hardening + deploy           | ☐ | ☐ | |

## Decisions made
- Auth: Google only, @kku.ac.th allowlist (confirmed by user). No payment.
- Template key-point table is a real Word table → docxtpl loops over rows using the
  {%tr for/endfor%} convention, each tag alone in its own row (open-tag row, body row,
  close-tag row) — putting both tags in the same row breaks docxtpl's regex.
- Multi-line table cells (เนื้อหา) need docxtpl's `{{r ... }}` RichText run-tag, not
  plain `{{ }}`, or the cell renders empty.
- วัตถุประสงค์ is a CLO-tied action statement per key point, never a copy of the title.
- ผลการเรียนรู้ column is COMPUTED from keyPoints[].cloRefs + CLOs[].ploRefs at render
  time (PLO{x}/CLO{y} pairs) — never authored as free text.
- Google OAuth client registered with explicit authorize/token URLs (no discovery-doc
  fetch) so /auth/login needs no network access and is fully unit-testable offline.
- LLM is NOT two separate provider SDKs — gen.ai.kku.ac.th is one OpenAI-compatible
  gateway that routes to Claude/GPT/others by `model` name. app/llm.py is a single
  `openai` SDK client pointed at that base_url; "switch by config" just changes the
  model string (LLM_PROVIDER=claude|gpt in .env), not the client class.
- docx loader walks the body in document order (paragraphs interleaved with tables),
  not "all paragraphs then all tables" — มคอ tables are meaningless out of context.
- Horizontally-merged table cells repeat the same cell object/text N times in
  `row.cells` (python-docx quirk, confirmed against the real PT.docx schedule table)
  → dedupe consecutive identical cells per row before joining, or every merged header
  cell prints 2-8x. PDF (PS.pdf) is explicitly NOT supported by M4 — out of CLAUDE.md's
  documented scope (pptx/docx only); flag if a real มคอ shows up as PDF.
- Real fixtures used for M4 tests instead of synthetic ones (tests/fixtures/PT.docx,
  Autonomic_Nervous_System.pptx) — fixtures live at repo-root tests/fixtures/, not
  backend/tests/fixtures/ (only dummy_lesson_plan_context.py lives under backend/).
- Real มคอ-3 specs legitimately have NO PLOs (DT.docx's PLO/CLO mapping table — section
  10 — is headers-only with empty rows; that section only applies to thesis-type
  courses). Extraction must return PLOs: [] in that case, never invent PLOs to fill
  the gap — confirmed correct in the M5 human-gate run.
- Schedule tables almost never state CLO ids per row directly — the extraction prompt
  has the LLM infer cloRefs by matching each lecture's topic/expected-outcome text
  against the course-level CLOs it already extracted. Best-effort; instructor corrects
  via M7's correction screen, not M5's job to be perfect.
- extraction_service.extract_course() is NOT covered by automated live-LLM tests (mocked
  provider only, per convention) — the human-gate proof lives in
  backend/extraction_proof/{DT,PT}.json, generated by a manual one-off script, not pytest.
- session_store is disk-backed JSON under repo-root sessions/ (gitignored), keyed by a
  uuid4 hex session id; tests monkeypatch session_store.SESSIONS_DIR to tmp_path for
  isolation rather than touching the real sessions/ dir.
- POST /api/session deliberately has NO matching GET endpoint yet — not in CLAUDE.md's
  documented API surface for M6, so left out rather than added speculatively. M7's
  GET/PUT /api/course/{sid} will be the first read path into session data.
- outline_service.generate_outline() recomputes totalDurationMin itself by summing the
  returned keyPoints — it does NOT trust whatever total the model states, and does NOT
  hard-fail if the sum drifts from the lecture's scheduled duration. "4-8 points
  summing to durationMin" is a prompt instruction/target, not a validator; M9's "live
  total" editor is where the instructor reconciles this, matching the M5 "best-effort,
  never block" philosophy.
- No /api/outline endpoint wired into main.py yet — M8 only built the core
  generate_outline() service (the part with a real test/build-order rationale). Wiring
  POST /api/outline needs M7's session["course"] (the corrected ExtractedCourse) to
  exist first, so the route is deferred to when M7 lands, not built speculatively now.

- Node.js/npm IS installed on this machine via nvm (`~/.nvm`, node v24.18.0, npm
  11.16.0) — it's just not on PATH by default in a fresh shell. Always run
  `export NVM_DIR="$HOME/.nvm"; source "$NVM_DIR/nvm.sh"` before any node/npm command.
  (Earlier sessions wrongly concluded Node wasn't installed at all — it was just not
  sourced. Always re-check with nvm before assuming it's missing.)
- frontend/ is a Vite+React scaffold (`npm create vite@latest -- --template react`),
  dev proxy in vite.config.js forwards /api and /auth to http://localhost:8000 so the
  two dev servers (vite on 5173, uvicorn on 8000) work together locally without CORS
  config. node_modules/ is gitignored; package-lock.json is committed.
- Browser verification used the Claude-in-Chrome MCP (navigate/read_page/form_input/
  computer click), not the Preview MCP — preview_start needs `.claude/launch.json`
  relative to the session's registered project root (webapp_kk1), but this app's
  actual code lives in the sibling dir `webapp kk2`, so Claude-in-Chrome against a
  manually-started dev server (plain `npm run dev` / `uvicorn` in the background) was
  simpler. Did NOT attempt actual Google login (that needs real credentials and is a
  prohibited action) — confirmed the redirect URL/params are correct and stopped there;
  post-login session creation is already covered by M6's mocked-auth test suite.

## Open questions / blockers
- (none blocking — Node is available; M7/M9/M10 frontend work can proceed normally)

## Next session should start by
- M7 (upload + correction screen) is next in build order — the load-bearing gate for
  messy input. Needs multipart upload UI + the GET/PUT /api/course/{sid} backend
  endpoints (not yet built) wired to extraction_service (M5) and session_store (M6).
