# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
====
Today's Schedule for Jordan's pets (Mochi, Luna)
============================================================
Plan for Monday 05 Oct 2026 (70/90 min used)
  07:00-07:10  Luna: Clean litter box (10 min, medium) - medium priority
  07:30-08:00  Mochi: Morning walk (30 min, high) - high priority, preferred 07:30
  08:15-08:25  Mochi: Breakfast (10 min, high) - high priority, preferred 08:15
  09:00-09:05  Luna: Thyroid meds (5 min, high) - high priority, preferred 09:00
  18:00-18:15  Luna: Brush fur (15 min, low) - low priority, preferred 18:00
Skipped:
  Mochi: Fetch in the yard - needs 45 min but only 20 min left
```

## 📐 Smarter Scheduling

All scheduling logic lives in [`pawpal_system.py`](pawpal_system.py). Run `python main.py` to see every feature below in action.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | By preferred time, or by priority then shortest duration |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.get_tasks()`, `Scheduler.get_due_tasks()` | By pet name, completion status, or due date |
| Time budget | `Scheduler.fits_in_time()`, `Scheduler.generate_plan()` | Greedy: skips tasks that don't fit and records why |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.generate_plan()` | Warns about overlapping time slots; plan shifts the later task |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()`, `Task.is_due()` | Completing a daily/weekly task creates the next occurrence |

### Sorting

- **`Scheduler.sort_by_time(pairs)`** orders tasks chronologically by their preferred `"HH:MM"` time. It compares real `time` objects rather than strings, so `"9:00"` correctly sorts before `"10:00"` (times are also zero-padded when a `Task` is created). Tasks without a preferred time go last.
- **`Scheduler.sort_tasks(pairs)`** orders tasks by priority (high → low), then shortest first, so the most important work is chosen first and more tasks fit in the time budget. This is the order the planner uses to decide what to include.

Both return a new list and never modify the input, so they can be chained with filtering.

### Filtering

- **`Scheduler.filter_tasks(pairs, pet_name=None, completed=None)`** keeps only tasks for a given pet and/or with a given completion status. Passing `None` means "don't filter on this", so either filter, both, or neither can be used.
- **`Scheduler.get_tasks(pet_name=None, completed=None)`** applies the same filters to every task across all of the owner's pets.
- **`Scheduler.get_due_tasks(on)`** returns only tasks that are not completed and whose due date has arrived. This is what the planner schedules from.

```python
# Mochi's open tasks in time order
scheduler.sort_by_time(scheduler.get_tasks(pet_name="Mochi", completed=False))
```

### Conflict detection

**`Scheduler.detect_conflicts(pairs=None, on=None)`** is a lightweight check that returns a list of warning strings instead of raising an error:

1. Keep only tasks that have a preferred time, and sort them by start time.
2. Compare each task with the ones after it. Two tasks conflict when the later one starts before the earlier one ends (so a 07:45 task clashes with a 07:30–08:00 walk, but a task starting exactly at 08:00 does not).
3. Because the list is sorted, stop comparing as soon as a task starts after the current one ends.

Conflicts are reported for the **same pet** and for **different pets**, since one owner can't do two things at once. `generate_plan()` runs this check, stores the messages in `DailyPlan.warnings`, and resolves each clash by moving the later task to the next free slot, so the final plan never overlaps.

```
WARNING: Mochi: Morning walk (07:30-08:00) overlaps Mochi: Ear drops (07:45-07:50) - same pet (Mochi)
WARNING: Mochi: Breakfast (08:15-08:25) overlaps Luna: Breakfast (08:15-08:20) - different pets (Mochi & Luna)
```

### Recurring tasks

Each task has a `frequency` of `"once"`, `"daily"` or `"weekly"`, and a `due_date`.

- **`Task.next_occurrence(completed_on)`** returns a fresh, uncompleted copy of a daily or weekly task, due 1 or 7 days after the day it was completed. It returns `None` for `"once"` tasks.
- **`Pet.complete_task(task_id, on)`** marks the task complete, keeps it as history, and adds the next occurrence with a new id. Completing the same task twice does not create a duplicate.
- **`Scheduler.mark_task_complete(pet_name, task_id, on)`** is the entry point used by `main.py` and the Streamlit **Mark complete** button.
- **`Task.is_due(on)`** keeps the next occurrence out of today's plan until its due date arrives.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
