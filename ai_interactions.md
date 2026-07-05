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

**Task chosen:** rescheduling a weekly task to its *next* occurrence. My
`Task.next_occurrence()` naively adds 7 days to `due_date`, which drifts if a
task is completed early or late. The harder version: given a target weekday and
today's date, return the next date that actually falls on that weekday.

**Prompt used (identical for both tools):**

> "In Python, write a function `next_weekly_date(target_weekday, after)` that
> returns the next `datetime.date` strictly after `after` whose weekday equals
> `target_weekday` (0=Mon..6=Sun). Handle the case where `after` already falls
> on the target weekday (it should roll forward a full week). Keep it short and
> explain the modular arithmetic."

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Opus 4.8 (Claude Code) | _TODO: paste the model you ran, e.g. Gemini / ChatGPT / Copilot_ |
| **Prompt** | (the prompt above) | (same prompt above) |
| **Response summary** | Returned the modular-arithmetic solution below; explained `(target - after.weekday()) % 7`, then `or 7` to force a roll-forward when the remainder is 0. | _TODO_ |
| **What was useful** | Correct, concise, and the `days_ahead or 7` trick handles the "already on that weekday" edge case in one line. Explanation named the edge case explicitly. | _TODO_ |
| **Problems noticed** | Did not validate `target_weekday` is in 0–6; "strictly after" vs "on or after" is a real ambiguity it resolved by assumption rather than asking. | _TODO_ |
| **Decision** | ✅ Chosen | _TODO_ |

**Claude's (Option A) solution:**

```python
from datetime import date, timedelta

def next_weekly_date(target_weekday: int, after: date) -> date:
    """Next date strictly after `after` whose weekday is target_weekday (0=Mon)."""
    days_ahead = (target_weekday - after.weekday()) % 7
    days_ahead = days_ahead or 7  # already on that weekday -> roll a full week
    return after + timedelta(days=days_ahead)
```

**Which approach did you use in your final implementation and why?**

I kept the Claude solution because the modular-arithmetic approach is the
standard, provably-correct way to find the next matching weekday, and the
`days_ahead or 7` line is the cleanest handling of the "today is already the
target weekday" edge case. _(Complete Option B by running the same prompt in a
second tool and note whether it produced the same core logic, added input
validation, or made a different assumption about the "strictly after" boundary.)_
