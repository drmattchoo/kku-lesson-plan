# Build progress

Read this first each session, then run the test suite. Update it as the LAST act
of every session.

## Status
Current session target: Phase 0 + Phase 1 + start of Phase 2 (M0, M1, M2, M3)
Last green commit: c66552c — "M3: LLM provider interface via KKU gateway (OpenAI-compatible, model-switched) ✓"
Tree state: ☑ green

## Your homework (do before opening Claude Code)
- [x] One clean official KKU lesson-plan .docx + written list of every field it needs
- [x] Google sign-in credentials (Google Cloud, restricted to kku.ac.th) — in .env
- [x] University API key + chosen model — KKU gateway (gen.ai.kku.ac.th) key in .env,
      verified live against both claude-sonnet-4.6 and gpt-5.5
- [ ] 2–3 REAL messy course specs to test extraction against (have curriculum/ samples,
      not yet confirmed as the real ones to extraction-test against for M5)

## Modules
| Phase | Module | Built | Tested | Notes |
|-------|--------|-------|--------|-------|
| 0 | M0  scaffold + config            | ☑ | ☑ | /health returns active model |
| 0 | M1  template binder + render proof [reuse] | ☑ | ☑ | GATE passed: human verified render_proof.docx vs KKU standard; objective/content tied to CLOs, ผลการเรียนรู้ column computed as PLO/CLO pairs |
| 1 | M2  Google sign-in (@kku.ac.th)  | ☑ | ☑ | Authlib + Starlette SessionMiddleware; /api/* guarded via require_kku_user; tests mock Google token, no network in test suite |
| 2 | M3  LLM provider interface       | ☑ | ☑ | app/llm.py — single OpenAI-SDK client against KKU gateway, model-switched; live-verified against claude-sonnet-4.6 + gpt-5.5 |
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
- LLM is NOT two separate provider SDKs — gen.ai.kku.ac.th is one OpenAI-compatible
  gateway that routes to Claude/GPT/others by `model` name. app/llm.py is a single
  `openai` SDK client pointed at that base_url; "switch by config" just changes the
  model string (LLM_PROVIDER=claude|gpt in .env), not the client class.

## Open questions / blockers
- No Node.js/npm on this machine — frontend (M6+) can be scaffolded as files but not
  installed, run, or verified until Node is available.
- Confirm the 2–3 curriculum/ sample specs (RT/PT/IL/PH/Nurse/DT/PS) are representative
  enough for M5 extraction testing, or if the user has other messier real มคอ-3 files.

## Next session should start by
- Building M4 (document loaders: pptx/docx -> structured text) and M5 (extraction
  service -> ExtractedCourse DRAFT) — both backend-only, no Node required. M5 needs the
  real messy มคอ-3 specs for its human gate.
