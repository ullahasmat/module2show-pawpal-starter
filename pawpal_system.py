"""PawPal+ logic layer.

Phase 1 skeleton: class names, attributes, and empty method stubs derived
from the UML in diagrams/uml.mmd. Scheduling logic is implemented in a later
phase -- for now the methods only declare intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional

# Ordering used to rank priorities (higher number = more urgent).
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}


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

    def priority_rank(self) -> int:
        """Return a numeric rank so tasks can be sorted by urgency."""
        raise NotImplementedError


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
        raise NotImplementedError


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
        raise NotImplementedError

    def all_tasks(self) -> list[Task]:
        """Collect the tasks across every pet this owner has."""
        raise NotImplementedError


class Scheduler:
    """Turns an owner's tasks + constraints into an ordered daily plan."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def available_minutes(self) -> int:
        """Minutes between the owner's available_start and available_end."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by the constraints that matter most (priority, etc.)."""
        raise NotImplementedError

    def expand_recurring(self, tasks: list[Task], day: date) -> list[Task]:
        """Materialize recurring tasks that are due on the given day."""
        raise NotImplementedError

    def detect_conflicts(
        self, plan: list[ScheduledTask]
    ) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Find pairs of scheduled tasks whose time ranges overlap."""
        raise NotImplementedError

    def build_plan(self, day: date) -> list[ScheduledTask]:
        """Produce the ordered, time-boxed plan for the given day."""
        raise NotImplementedError

    def explain(self, plan: list[ScheduledTask]) -> str:
        """Return a human-readable explanation of why the plan looks this way."""
        raise NotImplementedError
