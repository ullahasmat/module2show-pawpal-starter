"""Quick tests for PawPal+ core behaviors."""

from pawpal_system import Pet, Task


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
