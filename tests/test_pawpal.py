"""Tests for the core PawPal+ classes."""

import sys
from datetime import date, time
from pathlib import Path

import pytest

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


# --- Sorting ----------------------------------------------------------------

def descriptions(pairs):
    return [t.description for _, t in pairs]


def test_sort_by_time_orders_real_times_and_puts_untimed_last():
    owner, mochi, luna = make_owner_with_pets()
    mochi.add_task(Task("Dinner", time="10:00"))
    mochi.add_task(Task("Play"))  # no preferred time
    luna.add_task(Task("Breakfast", time="9:00"))  # normalised to "09:00"

    ordered = Scheduler(owner).sort_by_time(owner.get_all_tasks())

    assert descriptions(ordered) == ["Breakfast", "Dinner", "Play"]


def test_sort_tasks_priority_then_shortest_then_original_order():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Low", duration_minutes=5, priority="low"))
    mochi.add_task(Task("High long", duration_minutes=30, priority="high"))
    mochi.add_task(Task("High short A", duration_minutes=10, priority="high"))
    mochi.add_task(Task("High short B", duration_minutes=10, priority="high"))

    ordered = Scheduler(owner).sort_tasks(owner.get_all_tasks())

    assert descriptions(ordered) == ["High short A", "High short B", "High long", "Low"]


def test_sorts_handle_empty_input_and_do_not_mutate():
    owner, mochi, _ = make_owner_with_pets()
    scheduler = Scheduler(owner)
    assert scheduler.sort_tasks([]) == []
    assert scheduler.sort_by_time([]) == []

    mochi.add_task(Task("Late", priority="low", time="18:00"))
    mochi.add_task(Task("Early", priority="high", time="07:00"))
    pairs = owner.get_all_tasks()
    original = list(pairs)

    scheduler.sort_tasks(pairs)
    scheduler.sort_by_time(pairs)

    assert pairs == original


# --- Recurrence -------------------------------------------------------------

def test_late_completion_counts_from_completion_day():
    pet = Pet(name="Mochi", species="dog")
    walk = pet.add_task(Task("Walk", frequency="daily", due_date=date(2026, 10, 5)))

    next_walk = pet.complete_task(walk.task_id, on=date(2026, 10, 8))

    assert next_walk.due_date == date(2026, 10, 9)


def test_early_completion_of_weekly_task_counts_from_completion_day():
    # Documents current behaviour: completing before the due date is allowed
    # and the next occurrence counts from the day it was actually done.
    pet = Pet(name="Luna", species="cat")
    brush = pet.add_task(Task("Brush fur", frequency="weekly", due_date=date(2026, 10, 12)))

    next_brush = pet.complete_task(brush.task_id, on=date(2026, 10, 6))

    assert next_brush.due_date == date(2026, 10, 13)


def test_missed_days_do_not_pile_up():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Walk", frequency="daily", due_date=date(2026, 10, 5)))

    due = Scheduler(owner).get_due_tasks(date(2026, 10, 8))

    assert descriptions(due) == ["Walk"]


def test_completing_the_next_occurrence_chains_correctly():
    pet = Pet(name="Mochi", species="dog")
    first = pet.add_task(Task("Walk", frequency="daily"))

    second = pet.complete_task(first.task_id, on=date(2026, 10, 5))
    third = pet.complete_task(second.task_id, on=date(2026, 10, 6))

    assert len({first.task_id, second.task_id, third.task_id}) == 3
    assert third.due_date == date(2026, 10, 7)
    assert [t.completed for t in pet.get_tasks()] == [True, True, False]


def test_switching_frequency_to_once_stops_recurrence():
    pet = Pet(name="Mochi", species="dog")
    walk = pet.add_task(Task("Walk", frequency="daily"))
    pet.edit_task(walk.task_id, frequency="once")

    assert pet.complete_task(walk.task_id, on=date(2026, 10, 5)) is None
    assert len(pet.get_tasks()) == 1


# --- Planning: budget and placement -----------------------------------------

def test_task_exactly_filling_remaining_time_is_scheduled():
    owner, mochi, _ = make_owner_with_pets()
    owner.update_available_time(40)
    mochi.add_task(Task("Walk", duration_minutes=30, priority="high"))
    mochi.add_task(Task("Brush", duration_minutes=10, priority="low"))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    assert [e.task.description for e in plan.entries] == ["Walk", "Brush"]
    assert plan.skipped == []
    assert plan.total_minutes == 40


def test_zero_available_minutes_skips_everything():
    owner, mochi, _ = make_owner_with_pets()
    owner.update_available_time(0)
    mochi.add_task(Task("Walk", duration_minutes=30))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    assert plan.entries == []
    assert len(plan.skipped) == 1
    assert "Nothing scheduled." in plan.summary()


def test_greedy_skips_long_high_priority_but_keeps_shorter_low_priority():
    owner, mochi, _ = make_owner_with_pets()
    owner.update_available_time(20)
    mochi.add_task(Task("Long hike", duration_minutes=60, priority="high"))
    mochi.add_task(Task("Brush", duration_minutes=15, priority="low"))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    assert [e.task.description for e in plan.entries] == ["Brush"]
    assert plan.skipped[0].task.description == "Long hike"
    assert "needs 60 min but only 20 min left" in plan.skipped[0].reason


def test_preferred_time_before_plan_start_is_moved_to_start():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Early meds", duration_minutes=5, time="07:00"))

    plan = Scheduler(owner, start_time=time(8, 0)).generate_plan(date(2026, 10, 5))

    entry = plan.entries[0]
    assert entry.start == time(8, 0)
    assert "moved to 08:00" in entry.reason


def test_untimed_tasks_fill_gaps_only_when_they_fit():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Feed", duration_minutes=20, priority="high"))  # fits 08:00-08:20
    mochi.add_task(Task("Groom", duration_minutes=30, priority="medium"))  # would overrun 08:30
    mochi.add_task(Task("Vet call", duration_minutes=10, priority="high", time="08:30"))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    assert [(e.task.description, e.start) for e in plan.entries] == [
        ("Feed", time(8, 0)),
        ("Vet call", time(8, 30)),
        ("Groom", time(8, 40)),
    ]


def test_one_long_task_overlapping_two_short_ones_gives_two_warnings():
    owner, mochi, luna = make_owner_with_pets()
    mochi.add_task(Task("Walk", duration_minutes=60, time="08:00"))
    luna.add_task(Task("Breakfast", duration_minutes=10, time="08:10"))
    luna.add_task(Task("Meds", duration_minutes=5, time="08:30"))

    warnings = Scheduler(owner).detect_conflicts(on=date(2026, 10, 5))

    assert len(warnings) == 2
    assert all(w.startswith("Mochi: Walk") for w in warnings)


# --- Regressions: midnight wrap and update validation ---------------------

def test_conflict_detected_across_midnight():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Late walk", duration_minutes=30, time="23:50"))
    mochi.add_task(Task("Meds", duration_minutes=5, time="23:55"))

    assert len(Scheduler(owner).detect_conflicts(on=date(2026, 10, 5))) == 1


def test_plan_does_not_overlap_across_midnight():
    owner, mochi, _ = make_owner_with_pets()
    mochi.add_task(Task("Late walk", duration_minutes=30, priority="high", time="23:50"))
    mochi.add_task(Task("Meds", duration_minutes=5, priority="high", time="23:55"))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 5))

    walk, meds = plan.entries
    assert (walk.start, walk.end) == (time(23, 50), time(0, 20))
    assert meds.start == time(0, 20)  # pushed after the walk, not slotted inside it
    assert "moved to 00:20" in meds.reason


def test_failed_update_leaves_task_unchanged():
    task = Task("Walk", priority="high")

    with pytest.raises(ValueError):
        task.update(priority="urgent")

    assert task.priority == "high"


# --- Lookups and validation -------------------------------------------------

def test_unknown_ids_and_names_raise_key_error():
    owner, mochi, _ = make_owner_with_pets()
    with pytest.raises(KeyError):
        mochi.complete_task(999)
    with pytest.raises(KeyError):
        mochi.get_task(999)
    with pytest.raises(KeyError):
        owner.get_pet("Nobody")


def test_duplicate_pet_name_rejected():
    owner, _, _ = make_owner_with_pets()
    with pytest.raises(ValueError):
        owner.add_pet(Pet(name="Mochi", species="dog"))


@pytest.mark.parametrize("kwargs", [
    {"priority": "urgent"},
    {"frequency": "monthly"},
    {"duration_minutes": 0},
    {"time": "25:00"},
])
def test_invalid_task_fields_rejected(kwargs):
    with pytest.raises(ValueError):
        Task("Bad", **kwargs)
