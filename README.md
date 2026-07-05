# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

PawPal+ turns a list of pet care tasks into an ordered daily plan. The
scheduling logic lives in `pawpal_system.py` and is exposed through a Streamlit
UI (`app.py`).

- **Owner / Pet / Task model** — one owner has many pets, each pet has many
  tasks; tasks carry a duration, priority, category, recurrence, and an
  optional fixed start time.
- **Priority-aware daily planning** — `build_plan()` anchors fixed-time tasks,
  then greedily places the rest by priority into the earliest free slot inside
  the owner's available window, dropping tasks that don't fit.
- **Sorting by time** — `sort_by_time()` orders tasks chronologically, keeping
  untimed (flexible) tasks at the end; `sort_tasks()` orders by priority.
- **Filtering** — `filter_by_pet()` narrows tasks to one pet; `filter_by_status()`
  separates pending from completed tasks.
- **Recurring tasks** — completing a `daily` or `weekly` task auto-creates its
  next occurrence, advancing the due date with `timedelta` (daily → +1 day,
  weekly → +7 days).
- **Conflict warnings** — `conflict_warnings()` flags overlapping tasks (same
  pet or different pets) with a readable, non-crashing message.
- **Next available slot** — `next_available_slot()` answers "when could I fit a
  new task?" by finding the earliest free window of a given length in the day.
- **Plan explanations** — `explain()` prints why the plan looks the way it does.
- **Tested** — 15 pytest cases cover sorting, filtering, recurrence, conflicts,
  and edge cases.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running the CLI demo (`python main.py`) builds one owner (Jordan) with two pets
and eight tasks, then prints the plan the scheduler generates. Two tasks are
deliberately set to 07:30 to demonstrate conflict detection:

```
================================================
  Today's Schedule  (Sunday, July 05, 2026)
================================================
Daily plan for Jordan (window 07:00-20:00):
  07:00-07:05  Clean litter box for Luna (5 min, medium priority)
  07:05-07:20  Play / laser for Luna (15 min, low priority)
  07:30-07:35  Medication for Mochi (5 min, high priority) [fixed]
  07:30-07:40  Breakfast for Mochi (10 min, high priority) [fixed]
  07:45-07:55  Feeding for Luna (10 min, high priority) [fixed]
  08:00-08:30  Morning walk for Mochi (30 min, high priority) [fixed]
  08:30-08:50  Enrichment puzzle for Mochi (20 min, low priority)
  18:00-18:30  Evening walk for Mochi (30 min, medium priority) [fixed]
Warning -- 'Medication' (Mochi, 07:30-07:35) overlaps 'Breakfast' (Mochi, 07:30-07:40) [same pet]
------------------------------------------------
8 task(s) planned across 2 pet(s).
```

Fixed-time tasks are anchored to their exact time (`[fixed]`); flexible tasks
are slotted into the earliest free gap by priority.

## 🧪 Testing PawPal+

```bash
# Run the full test suite (use -m so imports resolve from the project root):
python -m pytest

# Run with coverage:
python -m pytest --cov
```

**What the tests cover** (`tests/test_pawpal.py`, 15 tests):

- **Model basics** — marking a task complete flips its status; adding a task grows a pet's task list.
- **Sorting** — `sort_by_time` returns timed tasks in clock order with flexible tasks last; `sort_tasks` orders by priority.
- **Filtering** — `filter_by_pet` (including an unknown-pet → empty case) and `filter_by_status` (excludes completed tasks).
- **Recurrence** — completing a daily task spawns a copy due the next day; weekly advances +7 days; a non-recurring task returns `None`; weekly tasks only appear on their weekday.
- **Conflict detection** — two tasks at the same time are flagged; tasks that merely touch at a boundary are not.
- **Planning edge cases** — an owner with no tasks yields an empty plan; a task too long for the available window is dropped.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/pjasmat/codepath/AI/module2show-pawpal-starter
collected 15 items

tests/test_pawpal.py ...............                                     [100%]

============================== 15 passed in 0.02s ===============================
```

**Confidence level: ★★★★☆ (4/5).** The core scheduling logic — sorting, filtering, recurrence, and conflict detection — is covered by focused happy-path and edge-case tests that all pass. I held back the fifth star because a few areas are still untested: overlapping *flexible* tasks packed around several fixed-time anchors, invalid input (e.g. an unknown priority string), and cross-pet conflicts. Those are the first cases I'd add next.

## 📐 Smarter Scheduling

The scheduling "brain" lives in `Scheduler` (in `pawpal_system.py`).
`Scheduler.build_plan(day)` orchestrates everything below: it expands
recurring tasks, anchors fixed-time tasks, then greedily places the remaining
tasks by priority into the earliest free slot inside the owner's window,
dropping any that no longer fit.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | `sort_tasks` orders by priority (high→low), then shortest duration as a tiebreaker. `sort_by_time` orders chronologically by `fixed_time`, pushing flexible (untimed) tasks to the end. |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | Filter tasks down to a single pet by name, or by completion status (`completed=False` returns pending tasks, `True` returns finished ones). |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()` | `detect_conflicts` returns overlapping pairs using full duration ranges (not just exact start times); `conflict_warnings` turns them into readable, non-crashing warning strings. Catches same-pet and cross-pet clashes. |
| Recurring tasks | `Scheduler.expand_recurring()`, `Task.next_occurrence()`, `Pet.complete_task()` | `expand_recurring` selects tasks due on a given day (`daily`, or `weekly` matched to a weekday). Completing a recurring task via `complete_task` auto-spawns its next occurrence, advancing the due date with `timedelta` (daily → +1 day, weekly → +1 week). |
| Next available slot | `Scheduler.next_available_slot()` | Given a duration, returns the earliest free `(start, end)` window in the day (or `None` if it can't fit), reusing the planner's earliest-fit search over the current plan. |

## 💾 Data Persistence

PawPal+ remembers your pets and tasks between runs by saving them to a
`data.json` file in the project root.

**How it works**

- Each class converts itself to and from a plain dict (`to_dict()` /
  `from_dict()`). This handles the fields JSON can't store natively: `time`
  values are saved as `"HH:MM"` strings and `date` values as ISO strings.
- `Owner.save_to_json(path)` writes the full owner → pets → tasks tree to JSON;
  `Owner.load_from_json(path)` rebuilds the objects from that file.
- In the Streamlit app, the owner is loaded from `data.json` on a cold start (if
  the file exists) and auto-saved back to `data.json` at the end of every run,
  so any change survives a restart. The sidebar **Reset** button deletes
  `data.json` so the reset sticks.
- `data.json` is user data, not code, so it is listed in `.gitignore`.

**Files modified for persistence**

- `pawpal_system.py` — added `to_dict`/`from_dict` to `Task`, `Pet`, and
  `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()`.
- `app.py` — load on cold start, auto-save each run, and clear the file on reset.
- `tests/test_pawpal.py` — a round-trip test (save then load preserves data).
- `.gitignore` — ignores the generated `data.json`.

## 📸 Demo Walkthrough

### Running the app

```bash
python -m streamlit run app.py
```

### What the UI lets you do

- **Sidebar — Owner:** set the owner's name and their available time window
  (when tasks may be scheduled), or reset everything.
- **Add a Pet:** enter a name, species, and optional breed. Submitting creates
  a real `Pet` object stored in `st.session_state`, so it persists across reruns.
- **Add a Task:** pick a pet, then set title, duration, priority, category,
  recurrence, and (optionally) a fixed start time or weekly weekday.
- **Tasks & Completion:** view tasks in time order, filter them by pet or by
  status (pending / completed / all), and mark a task complete.
- **Generate Schedule:** build today's plan and read the explanation of why it
  looks the way it does.

### Example workflow

1. In the sidebar, set the owner and available window (e.g. 07:00–20:00).
2. **Add a pet** — e.g. "Mochi" the dog.
3. **Add a few tasks** — a fixed 07:30 "Breakfast", a high-priority "Morning
   walk", and a `daily` "Enrichment puzzle".
4. Open **Tasks & Completion** to see them sorted by time; filter to just Mochi.
5. **Mark the daily task complete** — PawPal+ confirms it and auto-schedules the
   next occurrence for tomorrow.
6. Click **Generate Schedule** to see the ordered, time-boxed plan.

### Key Scheduler behaviors shown

- **Sorting** — the plan is ordered chronologically; flexible tasks fill gaps by
  priority.
- **Filtering** — the Tasks panel narrows by pet and by completion status.
- **Recurring auto-advance** — completing a daily/weekly task spawns its next
  occurrence.
- **Conflict warnings** — two tasks at the same time raise a non-blocking amber
  warning naming both tasks and their times.

### Sample CLI output (`python main.py`)

The demo script exercises the same logic without the UI. Note the 07:30 clash
that triggers a conflict warning, the chronological re-sort of out-of-order
tasks, the pet/status filters, and the recurring task spawning its next
occurrence:

```
================================================
  Today's Schedule  (Sunday, July 05, 2026)
================================================
Daily plan for Jordan (window 07:00-20:00):
  07:00-07:05  Clean litter box for Luna (5 min, medium priority)
  07:05-07:20  Play / laser for Luna (15 min, low priority)
  07:30-07:35  Medication for Mochi (5 min, high priority) [fixed]
  07:30-07:40  Breakfast for Mochi (10 min, high priority) [fixed]
  07:45-07:55  Feeding for Luna (10 min, high priority) [fixed]
  08:00-08:30  Morning walk for Mochi (30 min, high priority) [fixed]
  08:30-08:50  Enrichment puzzle for Mochi (20 min, low priority)
  18:00-18:30  Evening walk for Mochi (30 min, medium priority) [fixed]
Warning -- 'Medication' (Mochi, 07:30-07:35) overlaps 'Breakfast' (Mochi, 07:30-07:40) [same pet]
------------------------------------------------
8 task(s) planned across 2 pet(s).

================================================
  All tasks sorted by time
================================================
  07:30  Breakfast [high]
  07:30  Medication [high]
  07:45  Feeding [high]
  08:00  Morning walk [high]
  18:00  Evening walk [medium]
  --:-- (flexible)  Clean litter box [medium]
  --:-- (flexible)  Enrichment puzzle [low]
  --:-- (flexible)  Play / laser [low]

================================================
  Filter: Mochi's tasks only
================================================
  - Breakfast
  - Medication
  - Morning walk
  - Evening walk
  - Enrichment puzzle

================================================
  Recurring: complete a daily task -> next instance spawns
================================================
  Before: Mochi has 5 task(s).
  Completed 'Enrichment puzzle' (recurrence=daily).
  Auto-created next occurrence due 2026-07-06 (completed=False).
  After: Mochi has 6 task(s).
```

**Screenshots** *(optional, for human reviewers)*: <!-- Insert screenshots of the Streamlit app here if you like -->
