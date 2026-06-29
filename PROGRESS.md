# Build progress

Read this first each session, then run the test suite. Update it as the LAST act
of every session.

## Status
Current session target: _______  (e.g. "Phase 0: M0 + M1")
Last green commit: _______
Tree state: ☐ green  ☐ WIP (describe below)

## Your homework (do before opening Claude Code)
- [ ] One clean official KKU lesson-plan .docx + written list of every field it needs
- [ ] 2–3 REAL messy course specs to test extraction against
- [ ] Google sign-in credentials (Google Cloud, restricted to kku.ac.th)
- [ ] University API key + chosen model (GPT-5.5 or Sonnet)

## Modules
| Phase | Module | Built | Tested | Notes |
|-------|--------|-------|--------|-------|
| 0 | M0  scaffold + config            | ☐ | ☐ | |
| 0 | M1  template binder + render proof [reuse] | ☐ | ☐ | GATE: human verifies .docx vs KKU standard |
| 1 | M2  Google sign-in (@kku.ac.th)  | ☐ | ☐ | |
| 2 | M3  LLM provider interface       | ☐ | ☐ | |
| 2 | M4  document loaders [reuse]     | ☐ | ☐ | |
| 2 | M5  extraction service [reuse]   | ☐ | ☐ | best-effort; output is a DRAFT |
| 3 | M6  instructor form              | ☐ | ☐ | |
| 3 | M7  upload + correction screen   | ☐ | ☐ | the load-bearing gate for messy input |
| 3 | M8  outline service              | ☐ | ☐ | |
| 3 | M9  outline editor               | ☐ | ☐ | |
| 3 | M10 batch export                 | ☐ | ☐ | reuses M1 binder |
| 4 | M11 hardening + deploy           | ☐ | ☐ | |

## Decisions made
- Auth: Google only, @kku.ac.th allowlist. No payment.
- (e.g. "Template key-point table is a real Word table → docxtpl loops over rows")

## Open questions / blockers
- (e.g. "Confirm มคอ-3 stores CLO→PLO map as a table vs prose")

## Next session should start by
- 
