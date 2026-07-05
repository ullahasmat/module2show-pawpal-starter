"""Presentation helpers for PawPal+ (emoji + table formatting).

Kept separate from pawpal_system.py so the logic layer stays free of any
display concerns. Used by both the CLI demo (main.py) and the Streamlit UI
(app.py).
"""

from tabulate import tabulate

# Emoji per task category, so different kinds of care are visually scannable.
CATEGORY_EMOJI = {
    "walk": "🚶",
    "feeding": "🥣",
    "meds": "💊",
    "grooming": "🛁",
    "enrichment": "🧩",
    "general": "📌",
}

# Color-coded priority indicators.
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def category_icon(category: str) -> str:
    """Return an emoji for a task category (falls back to a pin)."""
    return CATEGORY_EMOJI.get(category, "📌")


def priority_label(priority: str) -> str:
    """Return a color dot + the priority word, e.g. '🔴 high'."""
    return f"{PRIORITY_EMOJI.get(priority, '⚪')} {priority}"


def status_icon(completed: bool) -> str:
    """Return a checkbox emoji for a task's completion status."""
    return "✅" if completed else "⬜"


def schedule_table(plan) -> str:
    """Render a list of ScheduledTask objects as a structured CLI table."""
    rows = [
        [
            f"{s.start:%H:%M}-{s.end:%H:%M}",
            f"{category_icon(s.task.category)} {s.task.title}",
            s.pet_name,
            priority_label(s.task.priority),
            "📌 fixed" if s.task.fixed_time else "flexible",
        ]
        for s in plan
    ]
    return tabulate(
        rows,
        headers=["Time", "Task", "Pet", "Priority", "Slot"],
        tablefmt="rounded_outline",
    )
