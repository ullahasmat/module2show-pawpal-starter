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

Running the CLI demo (`python main.py`) produces the schedule below. It builds
one owner (Jordan) with two pets and seven tasks, then prints the plan the
scheduler generates:

```
================================================
  Today's Schedule  (Sunday, July 05, 2026)
================================================
Daily plan for Jordan (window 07:00-20:00):
  07:00-07:05  Clean litter box for Luna (5 min, medium priority)
  07:05-07:20  Play / laser for Luna (15 min, low priority)
  07:30-07:40  Breakfast for Mochi (10 min, high priority) [fixed]
  07:45-07:55  Feeding for Luna (10 min, high priority) [fixed]
  08:00-08:30  Morning walk for Mochi (30 min, high priority) [fixed]
  08:30-08:50  Enrichment puzzle for Mochi (20 min, low priority)
  18:00-18:30  Evening walk for Mochi (30 min, medium priority) [fixed]
------------------------------------------------
7 task(s) planned across 2 pet(s).
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

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/pjasmat/codepath/AI/module2show-pawpal-starter
collected 2 items

tests/test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.01s ===============================
```

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

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
