"""Tests for PawPal+ core behaviors.

Grouped by feature: basic model behavior, sorting, filtering, recurrence, and
conflict detection. Each test builds a small owner/pet/task fixture so the
cases stay independent and easy to read.
"""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def make_owner(start=time(7, 0), end=time(20, 0)) -> Owner:
    """Return an owner with a single (empty) dog, ready to receive tasks."""
    owner = Owner(name="Jordan", available_start=start, available_end=end)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    return owner


# --- Basic model behavior -------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip a task's completed flag to True."""
    task = Task("Morning walk", 30, priority="high")
    assert task.completed is False  # tasks start incomplete

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should grow that pet's task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10, priority="high"))

    assert len(pet.tasks) == 1


# --- Sorting --------------------------------------------------------------

def test_sort_by_time_orders_chronologically():
    """sort_by_time() returns timed tasks in clock order, flexible ones last."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        Task("Evening walk", 30, fixed_time=time(18, 0)),
        Task("Flexible play", 15),  # no fixed_time -> should sort last
        Task("Breakfast", 10, fixed_time=time(7, 30)),
        Task("Lunch", 10, fixed_time=time(12, 0)),
    ]

    ordered = [t.title for t in scheduler.sort_by_time(tasks)]

    assert ordered == ["Breakfast", "Lunch", "Evening walk", "Flexible play"]


def test_sort_tasks_orders_by_priority():
    """sort_tasks() puts high-priority tasks before lower-priority ones."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        Task("Low job", 10, priority="low"),
        Task("High job", 10, priority="high"),
        Task("Medium job", 10, priority="medium"),
    ]

    ordered = [t.title for t in scheduler.sort_tasks(tasks)]

    assert ordered == ["High job", "Medium job", "Low job"]


def test_sort_by_priority_then_time():
    """Priority is the primary key; time only breaks ties within a priority.

    'Low early' is the earliest task but sorts last because it is low priority.
    """
    owner = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        Task("High late", 10, priority="high", fixed_time=time(18, 0)),
        Task("Low early", 10, priority="low", fixed_time=time(7, 0)),
        Task("High early", 10, priority="high", fixed_time=time(8, 0)),
        Task("Medium", 10, priority="medium", fixed_time=time(9, 0)),
    ]

    ordered = [t.title for t in scheduler.sort_by_priority_then_time(tasks)]

    assert ordered == ["High early", "High late", "Medium", "Low early"]


# --- Filtering ------------------------------------------------------------

def test_filter_by_pet_returns_only_that_pets_tasks():
    """filter_by_pet() returns tasks for the named pet and nothing else."""
    owner = make_owner()
    owner.add_pet(Pet(name="Luna", species="cat"))
    owner.pets[0].add_task(Task("Walk", 30))         # Mochi
    owner.pets[1].add_task(Task("Litter box", 5))    # Luna
    scheduler = Scheduler(owner)

    titles = [t.title for t in scheduler.filter_by_pet("Mochi")]

    assert titles == ["Walk"]


def test_filter_by_pet_unknown_name_returns_empty():
    """An unknown pet name yields an empty list rather than an error."""
    scheduler = Scheduler(make_owner())
    assert scheduler.filter_by_pet("Nobody") == []


def test_filter_by_status_excludes_completed():
    """filter_by_status(completed=False) drops tasks that are done."""
    owner = make_owner()
    done = Task("Done task", 10)
    done.mark_complete()
    owner.pets[0].add_task(done)
    owner.pets[0].add_task(Task("Pending task", 10))
    scheduler = Scheduler(owner)

    pending = [t.title for t in scheduler.filter_by_status(completed=False)]

    assert pending == ["Pending task"]


# --- Recurrence -----------------------------------------------------------

def test_complete_daily_task_spawns_next_day():
    """Completing a daily task creates a new instance due the following day."""
    pet = Pet(name="Mochi", species="dog")
    task = Task("Meds", 5, recurrence="daily", due_date=date(2026, 7, 5))
    pet.add_task(task)

    follow_up = pet.complete_task(task)

    assert task.completed is True                     # original is marked done
    assert follow_up is not None
    assert follow_up.completed is False               # the copy is fresh
    assert follow_up.due_date == date(2026, 7, 6)     # today + 1 day
    assert len(pet.tasks) == 2                         # original + spawned copy


def test_weekly_task_advances_seven_days():
    """A weekly task's next occurrence is due one week later."""
    task = Task("Bath", 30, recurrence="weekly", due_date=date(2026, 1, 1))
    follow_up = task.next_occurrence()
    assert follow_up.due_date == date(2026, 1, 8)


def test_non_recurring_task_has_no_next_occurrence():
    """A one-off ('none') task returns None instead of spawning a copy."""
    task = Task("Vet visit", 60, recurrence="none")
    assert task.next_occurrence() is None


def test_expand_recurring_weekly_only_on_matching_weekday():
    """A weekly task appears on its weekday and is skipped on others."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    # weekday=0 is Monday. 2026-07-06 is a Monday; 2026-07-07 is a Tuesday.
    weekly = Task("Grooming", 20, recurrence="weekly", weekday=0)

    on_monday = scheduler.expand_recurring([weekly], date(2026, 7, 6))
    on_tuesday = scheduler.expand_recurring([weekly], date(2026, 7, 7))

    assert weekly in on_monday
    assert weekly not in on_tuesday


# --- Conflict detection ---------------------------------------------------

def test_detect_conflicts_flags_two_tasks_at_same_time():
    """Two fixed-time tasks scheduled at the same time are flagged."""
    owner = make_owner()
    owner.pets[0].add_task(Task("Breakfast", 10, fixed_time=time(8, 0)))
    owner.pets[0].add_task(Task("Medication", 5, fixed_time=time(8, 0)))
    scheduler = Scheduler(owner)

    plan = scheduler.build_plan(date(2026, 7, 5))
    conflicts = scheduler.detect_conflicts(plan)

    assert len(conflicts) == 1
    assert len(scheduler.conflict_warnings(plan)) == 1


def test_adjacent_tasks_are_not_a_conflict():
    """Tasks that touch at a boundary (08:30 end / 08:30 start) do not clash."""
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, fixed_time=time(8, 0)))    # 08:00-08:30
    owner.pets[0].add_task(Task("Feed", 10, fixed_time=time(8, 30)))   # 08:30-08:40
    scheduler = Scheduler(owner)

    plan = scheduler.build_plan(date(2026, 7, 5))

    assert scheduler.detect_conflicts(plan) == []


# --- Planning edge cases --------------------------------------------------

def test_build_plan_with_no_tasks_is_empty():
    """An owner whose pet has no tasks produces an empty plan and a clear note."""
    scheduler = Scheduler(make_owner())
    plan = scheduler.build_plan(date(2026, 7, 5))

    assert plan == []
    assert scheduler.explain(plan) == "No tasks scheduled for this day."


def test_task_too_long_for_window_is_dropped():
    """A flexible task that cannot fit the available window is left out."""
    owner = make_owner(start=time(8, 0), end=time(8, 30))  # only 30 minutes
    owner.pets[0].add_task(Task("Long hike", 60))          # needs 60 minutes
    scheduler = Scheduler(owner)

    plan = scheduler.build_plan(date(2026, 7, 5))

    assert plan == []


# --- Next available slot (advanced capability) ----------------------------

def test_next_available_slot_finds_gap_after_fixed_task():
    """The earliest free slot starts right after an existing fixed task."""
    owner = make_owner(start=time(8, 0), end=time(10, 0))
    owner.pets[0].add_task(Task("Walk", 30, fixed_time=time(8, 0)))  # 08:00-08:30
    scheduler = Scheduler(owner)

    slot = scheduler.next_available_slot(date(2026, 7, 5), 30)

    assert slot == (time(8, 30), time(9, 0))


def test_next_available_slot_returns_none_when_day_is_full():
    """When the window is already filled, no slot is returned."""
    owner = make_owner(start=time(8, 0), end=time(8, 30))
    owner.pets[0].add_task(Task("Walk", 30, fixed_time=time(8, 0)))  # fills 08:00-08:30
    scheduler = Scheduler(owner)

    assert scheduler.next_available_slot(date(2026, 7, 5), 30) is None


# --- JSON persistence -----------------------------------------------------

def test_owner_json_round_trip(tmp_path):
    """Saving an owner to JSON and loading it back preserves pets and tasks."""
    owner = Owner("Jordan", time(7, 0), time(20, 0), preferred_categories=["walk"])
    pet = Pet("Mochi", "dog", "Shiba")
    pet.add_task(
        Task(
            "Walk",
            30,
            priority="high",
            fixed_time=time(8, 0),
            recurrence="daily",
            due_date=date(2026, 7, 5),
        )
    )
    owner.add_pet(pet)
    path = tmp_path / "data.json"

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded.name == "Jordan"
    assert loaded.available_start == time(7, 0)
    assert loaded.preferred_categories == ["walk"]
    assert len(loaded.pets) == 1
    assert loaded.pets[0].name == "Mochi"

    task = loaded.pets[0].tasks[0]
    assert task.title == "Walk"
    assert task.fixed_time == time(8, 0)          # time survived the round trip
    assert task.recurrence == "daily"
    assert task.due_date == date(2026, 7, 5)      # date survived the round trip
