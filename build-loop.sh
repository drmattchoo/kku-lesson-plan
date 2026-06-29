#!/usr/bin/env bash
# build-loop.sh — drive the module build with Claude Code in headless mode.
#
# WHAT THIS IS: a semi-automated builder. It loops over modules, asks Claude Code
# to build each one against the contract in CLAUDE.md, runs the tests, and commits
# only if they pass. You stop personally at the two HUMAN GATES (marked below).
#
# BILLING / LIMITS (read before running):
#  - On a Pro/Max SUBSCRIPTION: headless `claude -p` draws from a separate monthly
#    credit ($20 Pro / $100 Max5x / $200 Max20x), then it stops at the 5-hour or
#    weekly wall and waits for reset. It will NOT auto-resume — re-run this script
#    after the reset and it picks up at the first unchecked module.
#  - For truly unattended runs with no wall: authenticate Claude Code with an
#    API KEY (Claude Platform) instead — metered pay-as-you-go, no usage cap.
#  - Opus needs a Max plan or an API key (Pro has no Opus → M5 falls back to Sonnet).

set -euo pipefail

OPUS="opus-4.8"        # deep reasoning — use sparingly
SONNET="sonnet-4.6"    # the workhorse default
HAIKU="haiku-4.5"      # cheap/fast boilerplate

# module : model : one-line task (full contract lives in CLAUDE.md)
# Order matches the phases. Human gates are handled OUTSIDE the loop.
run_module () {
  local id="$1" model="$2" task="$3"
  echo "── $id  ($model) ──────────────────────────────"
  claude -p "Read CLAUDE.md. Build $id: $task. Write the test first, then the code. \
Stop when the test for $id is green. Do not touch other modules." \
    --model "$model" \
    --permission-mode acceptEdits \
    --allowedTools "Read,Write,Edit,Bash" \
    --max-turns 40 \
    --output-format json | jq -r '.result, "cost: \(.total_cost_usd // "n/a")"'

  # commit only if the suite passes
  if npm test --silent 2>/dev/null || pytest -q 2>/dev/null; then
    git add -A && git commit -m "$id ✓" >/dev/null
    echo "$id committed."
  else
    echo "!! $id tests not green — stopping so you can look. Nothing committed."
    exit 1
  fi
}

# ── PHASE 0 — prove the output ────────────────────────
run_module "M0" "$HAIKU"  "scaffold + config; /health returns the active model"
run_module "M1" "$SONNET" "template binder + render proof: dummy data -> .docx"
echo ">>> HUMAN GATE: open the rendered .docx in Word. Is it a real KKU lesson plan?"
echo ">>> Fix the template if not, then re-run. Build nothing else until this passes."
read -p "Press enter once the template output is approved... "

# ── PHASE 1 — the KKU door ────────────────────────────
run_module "M2" "$SONNET" "Google sign-in restricted to @kku.ac.th"

# ── PHASE 2 — tame the messy spec ─────────────────────
run_module "M3" "$SONNET" "LLM provider interface (GPT + Claude), schema-validated JSON"
run_module "M4" "$SONNET" "document loaders: pptx/docx -> structured text"
run_module "M5" "$OPUS"   "extraction service -> ExtractedCourse DRAFT, built for messy input"
echo ">>> HUMAN GATE: run M5 on your 2-3 REAL ugly specs. Can you fix wrong rows fast?"
read -p "Press enter once extraction quality on real files is acceptable... "

# ── PHASE 3 — wizard + loop ───────────────────────────
run_module "M6"  "$HAIKU"  "instructor form -> POST /api/session"
run_module "M7"  "$SONNET" "upload + correction screen (the editable gate)"
run_module "M8"  "$SONNET" "outline service -> LectureOutline (minutes sum, valid methods)"
run_module "M9"  "$SONNET" "outline editor: add/remove/reorder, live total, PUT"
run_module "M10" "$SONNET" "batch export: lectureId[] -> iterate outline+render -> .zip"

# ── PHASE 4 — hardening ───────────────────────────────
run_module "M11" "$SONNET" "retry-once on bad JSON, surface validation, persist session, rate-limit"

echo "All modules built. Update PROGRESS.md and deploy."
