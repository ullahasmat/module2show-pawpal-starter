"""PawPal+ logic layer.

The backend "brain" for PawPal+. Defines the data model (Task, ScheduledTask,
Pet, Owner) and the Scheduler that turns an owner's tasks plus constraints into
an ordered, time-boxed daily plan. This module has no UI dependencies so it can
be driven and tested from a plain CLI script.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date, time
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

    def priority_rank(self) -> int:
        """Return a numeric rank so tasks can be sorted by urgency."""
        return PRIORITY_ORDER.get(self.priority.lower(), 0)

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True


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

        conflicts = self.detect_conflicts(plan)
        if conflicts:
            lines.append("Warning -- overlapping fixed-time tasks:")
            for a, b in conflicts:
                lines.append(f"  - '{a.task.title}' overlaps '{b.task.title}'")

        return "\n".join(lines)
