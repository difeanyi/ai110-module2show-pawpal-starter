"""Tests for the core PawPal+ classes."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False

    task.mark_complete(on=date(2026, 10, 5))

    assert task.completed is True
    assert task.last_completed == date(2026, 10, 5)


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Breakfast", duration_minutes=10, priority="high"))
    assert len(pet.get_tasks()) == 1

    pet.add_task(Task("Evening walk", duration_minutes=20, priority="medium"))
    assert len(pet.get_tasks()) == 2
