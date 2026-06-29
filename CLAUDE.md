# แผนการสอน Generator — build context

Instructor web app for KKU faculty: reads a course spec (มคอ-3) and drafts a
KKU-format lesson plan one lecture at a time. The spec is the only REQUIRED input;
the instructor can optionally add existing slides and/or a short text brief to make
each generated outline more specific.
Pattern: **prove the output first → log in → tame messy input → generate in a loop → render**.

Some parsing / CLO-mapping / template logic can be lifted from the existing
`lesson-plan` skill — modules tagged [reuse] below.

## Three truths that shape the whole design
1. The OUTPUT (the KKU lesson-plan template) is the thing we CAN standardize — it's ours.
   So we lock and verify it FIRST, before building anything that feeds it.
2. The INPUT spec has NO standard and is messy. So the extractor is best-effort:
   the AI produces a DRAFT, and the instructor ALWAYS corrects it on screen.
   The correction screen is load-bearing, not optional.
3. The course spec is the ONLY required input. Slides and a short brief are OPTIONAL,
   interchangeable "grounding" for the outline step. Three modes:
     - spec alone    -> outline from topic + CLOs + model knowledge (generic but usable)
     - spec + slides -> outline grounded in the real material
     - spec + brief  -> outline grounded in the instructor's typed intent
   The outline service takes whatever grounding is available (slides text, brief text,
   or nothing) and adapts the prompt accordingly.

## Stack
- Backend: FastAPI (Python). Pydantic models double as the data schemas.
- Frontend: React + Vite — a wizard.
- Docs: python-pptx, python-docx (parse) · docxtpl (render).
- LLM: provider interface, GPT-5.5 + Claude Sonnet behind it, switch by config.
- Auth: Google sign-in, restricted to @kku.ac.th. No payment.
- State: one JSON blob per session (disk or SQLite). API key + Google secret server-side only.

## Data schemas (define once in schemas.py)
- InstructorProfile: name, title, department, faculty, university,
  courseCode, courseName, academicYear, semester, section
- ExtractedCourse: courseCode, courseName, PLOs[{id,text}],
  CLOs[{id,text,ploRefs[]}], lectures[{id,week,topic,name,durationMin,cloRefs[]}]
- OutlineGrounding (optional): { slidesText?, brief? }   # either, both, or neither
- LectureOutline: lectureId, totalDurationMin,
  keyPoints[{seq,title,objective,content,durationMin,teachingMethod,cloRefs[],materials,assessment}]
  -- teachingMethod in {lecture, interactive, quiz}; 4-8 points/60min, 5-10 min each, summing to durationMin
  -- objective MUST be a CLO-tied action statement, not a restatement of title: phrase it using
     the action verb from the CLO(s) in cloRefs applied to this point's subject (e.g. CLO "อธิบาย
     กลไก..." + point "ตัวรับในระบบประสาทอัตโนวัติ" -> objective "บอกชนิดของตัวรับในระบบประสาท
     อัตโนวัติได้"). content is a numbered list of subtopics, distinct from both title and objective.
     See the real filled example `template/แผนการสอนPT_ANS_2569.docx` for the target shape.
- LessonPlanContext = InstructorProfile + selected Lecture + its CLOs/PLOs + edited LectureOutline

## API
POST /api/session (InstructorProfile)              -> {sessionId}
POST /api/extract (multipart: มคอ [required] + slides [optional]) -> ExtractedCourse DRAFT
GET  /api/course/{sid}                              -> ExtractedCourse
PUT  /api/course/{sid}                              -> corrected ExtractedCourse   # correction gate
POST /api/outline ({lectureId, brief?})            -> LectureOutline draft  # uses slides/brief if present
PUT  /api/outline/{lid} (edited outline)           -> {ok, totalMin}
POST /api/export ({lectureId})                      -> .docx
POST /api/export/batch ({lectureIds[]})             -> .zip   # the loop

## Build order — do in THIS sequence, each ends GREEN + committed

### Phase 0 — Prove the output (build nothing else until this passes)
- [ ] M0  scaffold + config (env -> config, provider factory stub) — /health returns active model
- [ ] M1  template binder + render proof [reuse] — dummy data -> .docx; HUMAN opens in Word and
          confirms it matches the official KKU standard. This is the gate for everything else.

### Phase 1 — The KKU door
- [ ] M2  Google sign-in — restrict to @kku.ac.th, block everyone else

### Phase 2 — Tame the messy spec
- [ ] M3  LLM provider interface — both providers return schema-valid JSON; factory switches by config
- [ ] M4  document loaders [reuse] — pptx/docx -> structured text; SLIDES OPTIONAL (handle "none")
- [ ] M5  extraction service [reuse] — spec text -> ExtractedCourse DRAFT (spec-driven; built for mess)

### Phase 3 — Wizard + lesson-plan loop
- [ ] M6  instructor form (Stage 1) -> POST /api/session
- [ ] M7  upload (spec required, slides optional) + CORRECTION screen — show draft, instructor fixes, PUT
- [ ] M8  outline service (Stage 4) — lectureId (+ optional slides/brief) -> LectureOutline.
          Prompt adapts: if grounding present, base key points on it; else derive from topic + CLOs.
          UI exposes an optional "brief" text box at the outline step.
- [ ] M9  outline editor (Stage 5) — add/remove/reorder, live total, PUT
- [ ] M10 batch export (Stages 6-7) — lectureId[] -> iterate outline+render (reuses M1) -> .zip

### Phase 4 — Hardening + deploy
- [ ] M11 retry-once on bad JSON, surface validation, persist session, rate-limit; then deploy / hand to IT

## Build models (Claude Code) — set per `claude -p` invocation, don't switch mid-session
- Haiku 4.5  : trivial scaffolding (M0, M6)
- Sonnet 4.6 : the bulk (M1-M4, M7-M11)
- Opus 4.8   : M5 extraction (hardest reasoning) + gnarly debugging. (Pro has no Opus -> Sonnet.)

## Conventions (keep the build reset-proof)
- One module = one unit of work. Don't start a module you can't finish AND test this session.
- Test-first. Each module's one-line test above becomes a real test.
- MOCK THE LLM in tests — record one real response per service as a fixture, replay it.
  Never hit the live model in a test loop (saves API + usage budget).
- Commit per module: "M5: extraction service ✓".
- End every session at a passing-test state. Update PROGRESS.md as the last act.
- Secrets in .env only — never in client JS, never in a response body.

## Current state
See PROGRESS.md. Start each session by reading it and running the test suite.
