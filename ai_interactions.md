# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to add a third algorithmic capability beyond the core
requirements — a "next available slot" finder that, given a task duration,
returns the earliest free time window in the day — and to wire it through the
whole project (logic, tests, CLI demo, UI, diagram, and docs).

**What did the agent do?**

Files modified:

- `pawpal_system.py` — added `Scheduler.next_available_slot(day, duration_minutes)`,
  which builds the current plan, treats every scheduled task as busy, and reuses
  the existing `_earliest_free()` helper to find the first gap.
- `tests/test_pawpal.py` — added two tests: one that a 30-min slot lands right
  after a fixed 08:00–08:30 task, and one that a full day returns `None`.
- `main.py` — added a CLI section that prints the next free 45-minute slot.
- `app.py` — added a "🔍 Find a free slot for a new task" expander that calls
  the new method and shows the result with `st.success` / `st.warning`.
- `diagrams/uml.mmd` and `diagrams/uml_final.mmd` — added the new method to the
  `Scheduler` class.
- `README.md` — added a Features bullet and a Smarter Scheduling table row.

Commands run: `python -m pytest` (17 passed) and `python main.py` (printed a
free slot at 08:50–09:35).

**What did you have to verify or fix manually?**

- I verified the returned slot was correct by checking it started exactly when
  the previous task ended, and by confirming the two new tests and all 15 prior
  tests still pass.
- I reviewed the design choice to **reuse** `_earliest_free()` and `build_plan()`
  rather than write a new packing routine — this kept the feature small and
  consistent with the existing planner instead of duplicating logic.
- I noted a known interaction: because recurring tasks appear via
  `expand_recurring` regardless of due date, a spawned "tomorrow" instance still
  counts as busy time in today's plan. That is the same two-mechanism
  simplification documented in the reflection, not a new bug, so I left it.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
