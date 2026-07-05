"""PawPal+ logic layer.

The backend "brain" for PawPal+. Defines the data model (Task, ScheduledTask,
Pet, Owner) and the Scheduler that turns an owner's tasks plus constraints into
an ordered, time-boxed daily plan. This module has no UI dependencies so it can
be driven and tested from a plain CLI script.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from typing import Optional

# Ordering used to rank priorities (higher number = more urgent).
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}


def _to_minutes(t: time) -> int:
    """Convert a wall-clock time to minutes since midnight."""
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    """Convert minutes since midnight back to a time, clamped to a valid day."""
    m = max(0, min(m, 24 * 60 - 1))
    return time(hour=m // 60, minute=m % 60)


@dataclass
class Task:
    """A single unit of pet care work (a walk, feeding, med, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    category: str = "general"
    recurrence: str = "none"  # "none" | "daily" | "weekly"
    fixed_time: Optional[time] = None  # set when the task must happen at a specific time
    weekday: Optional[int] = None  # 0=Mon .. 6=Sun; anchors a "weekly" recurrence
    completed: bool = False
    due_date: Optional[date] = None  # the date this specific instance is due

    def priority_rank(self) -> int:
        """Return a numeric rank so tasks can be sorted by urgency."""
        return PRIORITY_ORDER.get(self.priority.lower(), 0)

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Return a fresh, uncompleted copy of this task for its next due date.

        Daily tasks advance by one day and weekly tasks by one week; using
        timedelta keeps month/year rollovers correct (e.g. Jan 31 -> Feb 1).
        Returns None for non-recurring ("none") tasks.
        """
        if self.recurrence == "daily":
            step = timedelta(days=1)
        elif self.recurrence == "weekly":
            step = timedelta(weeks=1)
        else:
            return None
        base = self.due_date or date.today()
        return replace(self, completed=False, due_date=base + step)


@dataclass
class ScheduledTask:
    """A Task placed on the day's timeline with a concrete start/end.

    A daily plan is a list of these, not raw Tasks -- this is what lets the
    scheduler time-box the day and detect overlaps.
    """

    task: Task
    start: time
    end: time
    pet_name: str = ""  # which pet the task belongs to, for display


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and, if it recurs, queue its next occurrence.

        Returns the newly spawned follow-up task, or None when the task does
        not recur. The original completed task is kept as history.
        """
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            self.tasks.append(follow_up)
        return follow_up


@dataclass
class Owner:
    """The person planning care, plus their scheduling preferences."""

    name: str
    available_start: time
    available_end: time
    preferred_categories: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Collect the tasks across every pet this owner has."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Turns an owner's tasks + constraints into an ordered daily plan."""

    def __init__(self, owner: Owner) -> None:
        """Bind the scheduler to the owner whose tasks it will plan."""
        self.owner = owner

    def available_minutes(self) -> int:
        """Minutes between the owner's available_start and available_end."""
        return _to_minutes(self.owner.available_end) - _to_minutes(
            self.owner.available_start
        )

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by urgency: highest priority first, then shortest
        duration as a tiebreaker, then title for a stable ordering."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_rank(), t.duration_minutes, t.title),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks chronologically by their ``fixed_time``.

        The lambda key is a tuple: the first element (``fixed_time is None``)
        keeps flexible tasks -- which have no set time -- at the end, and the
        second sorts the timed tasks by minutes-since-midnight. Priority breaks
        ties among the flexible tasks.
        """
        return sorted(
            tasks,
            key=lambda t: (
                t.fixed_time is None,  # False (0) before True (1): timed tasks first
                _to_minutes(t.fixed_time) if t.fixed_time is not None else 0,
                -t.priority_rank(),
            ),
        )

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return the tasks belonging to the pet with the given name."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                return list(pet.tasks)
        return []

    def filter_by_status(self, completed: bool = False) -> list[Task]:
        """Return the owner's tasks matching a completion status.

        Defaults to pending tasks (``completed=False``); pass ``True`` to get
        the finished ones.
        """
        return [t for t in self.owner.all_tasks() if t.completed == completed]

    def expand_recurring(self, tasks: list[Task], day: date) -> list[Task]:
        """Return the subset of tasks that actually happen on ``day``.

        - ``none``   : a one-off task; treated as due today.
        - ``daily``  : always due.
        - ``weekly`` : due only when ``weekday`` matches ``day`` (or when no
                       weekday is set, in which case it is treated as due).
        """
        due: list[Task] = []
        for t in tasks:
            if t.recurrence == "weekly":
                if t.weekday is None or t.weekday == day.weekday():
                    due.append(t)
            else:
                # "none", "daily", or any unknown value falls through to due.
                due.append(t)
        return due

    def _pet_lookup(self) -> dict[int, str]:
        """Map each task's identity to the name of the pet that owns it."""
        return {
            id(task): pet.name for pet in self.owner.pets for task in pet.tasks
        }

    @staticmethod
    def _earliest_free(
        window_start: int,
        window_end: int,
        duration: int,
        busy: list[tuple[int, int]],
    ) -> Optional[int]:
        """Return the earliest minute >= ``window_start`` where a task of
        ``duration`` minutes fits without overlapping any ``busy`` interval and
        still ends by ``window_end``. Returns None if it cannot fit."""
        candidate = window_start
        for b_start, b_end in sorted(busy):
            if b_end <= candidate:
                continue  # this busy block is already behind us
            if candidate + duration <= b_start:
                return candidate  # fits in the gap before this block
            candidate = max(candidate, b_end)  # bump past the overlap
        if candidate + duration <= window_end:
            return candidate
        return None

    def build_plan(self, day: date) -> list[ScheduledTask]:
        """Produce the ordered, time-boxed plan for ``day``.

        Strategy: expand recurring tasks, drop completed ones, anchor any
        fixed-time tasks, then greedily place the remaining (flexible) tasks by
        priority into the earliest free slot inside the owner's window. Tasks
        that cannot fit the window are dropped.
        """
        pet_of = self._pet_lookup()
        window_start = _to_minutes(self.owner.available_start)
        window_end = _to_minutes(self.owner.available_end)

        due = [t for t in self.expand_recurring(self.owner.all_tasks(), day) if not t.completed]
        fixed = [t for t in due if t.fixed_time is not None]
        flexible = self.sort_tasks([t for t in due if t.fixed_time is None])

        plan: list[ScheduledTask] = []
        busy: list[tuple[int, int]] = []

        # 1) Anchor fixed-time tasks exactly where they must happen.
        for t in fixed:
            start = _to_minutes(t.fixed_time)
            end = start + t.duration_minutes
            plan.append(
                ScheduledTask(t, _from_minutes(start), _from_minutes(end), pet_of.get(id(t), ""))
            )
            busy.append((start, end))

        # 2) Greedily place flexible tasks in the earliest slot that fits.
        for t in flexible:
            start = self._earliest_free(window_start, window_end, t.duration_minutes, busy)
            if start is None:
                continue  # no room left in the day -> dropped
            end = start + t.duration_minutes
            plan.append(
                ScheduledTask(t, _from_minutes(start), _from_minutes(end), pet_of.get(id(t), ""))
            )
            busy.append((start, end))

        plan.sort(key=lambda s: (_to_minutes(s.start), _to_minutes(s.end)))
        return plan

    def detect_conflicts(
        self, plan: list[ScheduledTask]
    ) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Find pairs of scheduled tasks whose time ranges overlap.

        Flexible tasks are placed without overlap by construction, so in
        practice this surfaces clashes between fixed-time tasks.
        """
        conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []
        for a, b in itertools.combinations(plan, 2):
            a_start, a_end = _to_minutes(a.start), _to_minutes(a.end)
            b_start, b_end = _to_minutes(b.start), _to_minutes(b.end)
            if a_start < b_end and b_start < a_end:
                conflicts.append((a, b))
        return conflicts

    def conflict_warnings(self, plan: list[ScheduledTask]) -> list[str]:
        """Return a readable warning string for each overlapping pair.

        Lightweight and non-fatal: it never raises. An empty list means the
        plan is conflict-free. Same-pet and cross-pet overlaps are both caught.
        """
        warnings: list[str] = []
        for a, b in self.detect_conflicts(plan):
            a_pet = a.pet_name or "?"
            b_pet = b.pet_name or "?"
            same = "same pet" if a.pet_name == b.pet_name else "different pets"
            warnings.append(
                f"'{a.task.title}' ({a_pet}, {a.start:%H:%M}-{a.end:%H:%M}) overlaps "
                f"'{b.task.title}' ({b_pet}, {b.start:%H:%M}-{b.end:%H:%M}) [{same}]"
            )
        return warnings

    def explain(self, plan: list[ScheduledTask]) -> str:
        """Return a human-readable explanation of the plan."""
        if not plan:
            return "No tasks scheduled for this day."

        window = f"{self.owner.available_start:%H:%M}-{self.owner.available_end:%H:%M}"
        lines = [f"Daily plan for {self.owner.name} (window {window}):"]
        for s in plan:
            who = f" for {s.pet_name}" if s.pet_name else ""
            anchored = " [fixed]" if s.task.fixed_time is not None else ""
            lines.append(
                f"  {s.start:%H:%M}-{s.end:%H:%M}  {s.task.title}{who} "
                f"({s.task.duration_minutes} min, {s.task.priority} priority){anchored}"
            )

        for warning in self.conflict_warnings(plan):
            lines.append(f"Warning -- {warning}")

        return "\n".join(lines)
