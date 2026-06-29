# Build progress

Read this first each session, then run the test suite. Update it as the LAST act
of every session.

## Status
Current session target: Phase 0 + Phase 1 (M0, M1, M2)
Last green commit: a7aeaad — "M2: Google sign-in restricted to @kku.ac.th, session cookie, /api/* guard ✓"
Tree state: ☑ green

## Your homework (do before opening Claude Code)
- [x] One clean official KKU lesson-plan .docx + written list of every field it needs
- [x] Google sign-in credentials (Google Cloud, restricted to kku.ac.th) — in .env
- [ ] 2–3 REAL messy course specs to test extraction against (have curriculum/ samples,
      not yet confirmed as the real ones to extraction-test against for M5)
- [ ] University API key + chosen model (GPT-5.5 or Sonnet) — ANTHROPIC_API_KEY/OPENAI_API_KEY
      still blank in .env, needed before M3/M5 can be exercised against a live model

## Modules
| Phase | Module | Built | Tested | Notes |
|-------|--------|-------|--------|-------|
| 0 | M0  scaffold + config            | ☑ | ☑ | /health returns active model |
| 0 | M1  template binder + render proof [reuse] | ☑ | ☑ | GATE passed: human verified render_proof.docx vs KKU standard; objective/content tied to CLOs, ผลการเรียนรู้ column computed as PLO/CLO pairs |
| 1 | M2  Google sign-in (@kku.ac.th)  | ☑ | ☑ | Authlib + Starlette SessionMiddleware; /api/* guarded via require_kku_user; tests mock Google token, no network in test suite |
| 2 | M3  LLM provider interface       | ☐ | ☐ | blocked on ANTHROPIC_API_KEY/OPENAI_API_KEY in .env |
| 2 | M4  document loaders [reuse]     | ☐ | ☐ | |
| 2 | M5  extraction service [reuse]   | ☐ | ☐ | best-effort; output is a DRAFT |
| 3 | M6  instructor form              | ☐ | ☐ | needs Node/npm — not installed on this machine yet |
| 3 | M7  upload + correction screen   | ☐ | ☐ | the load-bearing gate for messy input |
| 3 | M8  outline service              | ☐ | ☐ | |
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

## Open questions / blockers
- No Node.js/npm on this machine — frontend (M6+) can be scaffolded as files but not
  installed, run, or verified until Node is available.
- Need the university LLM API key (GPT-5.5 or Claude) before M3 can be built against
  a live model — currently blank in .env.
- Confirm the 2–3 curriculum/ sample specs (RT/PT/IL/PH/Nurse/DT/PS) are representative
  enough for M5 extraction testing, or if the user has other messier real มคอ-3 files.

## Next session should start by
- Filling ANTHROPIC_API_KEY (or OPENAI_API_KEY) in .env, then building M3 (LLM provider
  interface) and M4 (document loaders) — both backend-only, no Node required.
