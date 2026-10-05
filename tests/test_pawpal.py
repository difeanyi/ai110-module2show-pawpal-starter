"""Tests for the core PawPal+ classes."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Scheduler, Task


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


def make_scheduler():
    owner = Owner(name="Jordan", available_minutes=90)
    mochi, luna = Pet(name="Mochi", species="dog"), Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", duration_minutes=30, priority="high"))
    mochi.add_task(Task("Breakfast", duration_minutes=10, priority="high"))
    luna.add_task(Task("Litter box", duration_minutes=10, priority="medium"))
    mochi.tasks[1].mark_complete(on=date(2026, 10, 5))
    return Scheduler(owner)


def test_filter_by_pet_name():
    scheduler = make_scheduler()
    names = [t.description for _, t in scheduler.filter_tasks(scheduler.get_tasks(), pet_name="Mochi")]
    assert names == ["Walk", "Breakfast"]


def test_filter_by_completion_status():
    scheduler = make_scheduler()
    assert [t.description for _, t in scheduler.get_tasks(completed=True)] == ["Breakfast"]
    assert [t.description for _, t in scheduler.get_tasks(completed=False)] == ["Walk", "Litter box"]


def test_filter_by_pet_and_status_combined():
    scheduler = make_scheduler()
    assert [t.description for _, t in scheduler.get_tasks(pet_name="Mochi", completed=False)] == ["Walk"]
    assert scheduler.get_tasks(pet_name="Nobody") == []


def test_completing_daily_task_creates_next_day_instance():
    pet = Pet(name="Mochi", species="dog")
    walk = pet.add_task(Task("Walk", duration_minutes=30, priority="high", time="07:30", frequency="daily"))

    next_walk = pet.complete_task(walk.task_id, on=date(2026, 10, 5))

    assert walk.completed is True
    assert next_walk is not None and next_walk is not walk
    assert next_walk.completed is False
    assert next_walk.due_date == date(2026, 10, 6)
    assert next_walk.task_id != walk.task_id
    assert (next_walk.description, next_walk.time, next_walk.priority) == ("Walk", "07:30", "high")
    assert len(pet.get_tasks()) == 2


def test_completing_weekly_task_creates_instance_one_week_later():
    pet = Pet(name="Luna", species="cat")
    brush = pet.add_task(Task("Brush fur", frequency="weekly"))

    next_brush = pet.complete_task(brush.task_id, on=date(2026, 10, 5))

    assert next_brush.due_date == date(2026, 10, 12)
    assert not next_brush.is_due(date(2026, 10, 11))
    assert next_brush.is_due(date(2026, 10, 12))


def test_completing_once_task_creates_nothing():
    pet = Pet(name="Mochi", species="dog")
    vet = pet.add_task(Task("Vet visit", frequency="once"))

    assert pet.complete_task(vet.task_id, on=date(2026, 10, 5)) is None
    assert len(pet.get_tasks()) == 1


def test_completing_twice_does_not_duplicate():
    pet = Pet(name="Mochi", species="dog")
    walk = pet.add_task(Task("Walk", frequency="daily"))

    pet.complete_task(walk.task_id, on=date(2026, 10, 5))
    assert pet.complete_task(walk.task_id, on=date(2026, 10, 5)) is None
    assert len(pet.get_tasks()) == 2


def test_next_occurrence_not_scheduled_until_due():
    scheduler = make_scheduler()
    walk_id = scheduler.owner.get_pet("Mochi").tasks[0].task_id
    scheduler.mark_task_complete("Mochi", walk_id, on=date(2026, 10, 5))

    today = [t.description for _, t in scheduler.get_due_tasks(date(2026, 10, 5))]
    tomorrow = [t.description for _, t in scheduler.get_due_tasks(date(2026, 10, 6))]
    assert "Walk" not in today
    assert "Walk" in tomorrow


def make_owner_with_pets():
    owner = Owner(name="Jordan", available_minutes=120)
    mochi, luna = Pet(name="Mochi", species="dog"), Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_detects_same_time_conflict_across_pets():
    owner, mochi, luna = make_owner_with_pets()
    mochi.add_task(Task("Breakfast", duration_minutes=10, time="08:00"))
    luna.add_task(Task("Breakfast", duration_minutes=5, time="08:00"))

    warnings = Scheduler(owner).detect_conflicts(on=date(2026, 10, 5))

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_detects_overlapping_tasks_for_same_pet():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Walk", duration_minutes=30, time="07:30"))
    mochi.add_task(Task("Ear drops", duration_minutes=5, time="07:45"))

    warnings = Scheduler(owner).detect_conflicts(on=date(2026, 10, 5))

    assert len(warnings) == 1
    assert "same pet (Mochi)" in warnings[0]


def test_back_to_back_and_untimed_tasks_are_not_conflicts():
    owner, mochi, luna = make_owner_with_pets()
    mochi.add_task(Task("Walk", duration_minutes=30, time="07:30"))
    luna.add_task(Task("Breakfast", duration_minutes=5, time="08:00"))  # starts exactly when walk ends
    luna.add_task(Task("Litter box", duration_minutes=10))  # no preferred time

    assert Scheduler(owner).detect_conflicts(on=date(2026, 10, 5)) == []


def test_plan_includes_conflict_warning_and_does_not_overlap():
    owner, mochi, luna = make_owner_with_pets()
    mochi.add_task(Task("Breakfast", duration_minutes=10, priority="high", time="08:00"))
    luna.add_task(Task("Breakfast", duration_minutes=5, priority="high", time="08:00"))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    assert len(plan.warnings) == 1
    first, second = plan.entries
    assert second.start >= first.end
