"""PawPal+ demo script (CLI testing ground).

Builds a small scenario -- one owner, two pets, several tasks -- and prints
today's generated schedule to the terminal. Run it with: python main.py
"""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and a handful of tasks."""
    owner = Owner(
        name="Jordan",
        available_start=time(7, 0),
        available_end=time(20, 0),
        preferred_categories=["walk", "meds"],
    )

    # Pet 1: a dog with time-anchored and flexible tasks.
    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu")
    mochi.add_task(Task("Breakfast", 10, priority="high", category="feeding", fixed_time=time(7, 30)))
    mochi.add_task(Task("Morning walk", 30, priority="high", category="walk", fixed_time=time(8, 0)))
    mochi.add_task(Task("Evening walk", 30, priority="medium", category="walk", fixed_time=time(18, 0)))
    mochi.add_task(Task("Enrichment puzzle", 20, priority="low", category="enrichment", recurrence="daily"))
    owner.add_pet(mochi)

    # Pet 2: a cat with its own tasks.
    luna = Pet(name="Luna", species="cat", breed="Tabby")
    luna.add_task(Task("Feeding", 10, priority="high", category="feeding", fixed_time=time(7, 45)))
    luna.add_task(Task("Clean litter box", 5, priority="medium", category="grooming"))
    luna.add_task(Task("Play / laser", 15, priority="low", category="enrichment"))
    owner.add_pet(luna)

    return owner


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    today = date.today()

    plan = scheduler.build_plan(today)

    print("=" * 48)
    print(f"  Today's Schedule  ({today:%A, %B %d, %Y})")
    print("=" * 48)
    print(scheduler.explain(plan))
    print("-" * 48)
    print(f"{len(plan)} task(s) planned across {len(owner.pets)} pet(s).")

    # --- Sorting: tasks were added out of order; sort_by_time fixes that -----
    print("\n" + "=" * 48)
    print("  All tasks sorted by time")
    print("=" * 48)
    for t in scheduler.sort_by_time(owner.all_tasks()):
        when = t.fixed_time.strftime("%H:%M") if t.fixed_time else "--:-- (flexible)"
        print(f"  {when}  {t.title} [{t.priority}]")

    # --- Filtering: by pet ---------------------------------------------------
    print("\n" + "=" * 48)
    print("  Filter: Mochi's tasks only")
    print("=" * 48)
    for t in scheduler.filter_by_pet("Mochi"):
        print(f"  - {t.title}")

    # --- Filtering: by status (mark one done, then list what's pending) ------
    owner.all_tasks()[0].mark_complete()
    print("\n" + "=" * 48)
    print("  Filter: pending tasks (after marking one complete)")
    print("=" * 48)
    for t in scheduler.filter_by_status(completed=False):
        print(f"  - {t.title}")


if __name__ == "__main__":
    main()
