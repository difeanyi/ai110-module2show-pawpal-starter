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

Run the full test suite from the project root:

```bash
python -m pytest
```

The 37 tests in [`tests/test_pawpal.py`](tests/test_pawpal.py) cover:

- **Sorting**: chronological order by preferred time (`"9:00"` before `"10:00"`, untimed tasks last); priority then shortest duration, with stable ties; empty input; inputs never mutated.
- **Filtering**: by pet name, completion status, and both combined.
- **Recurring tasks**: daily/weekly tasks create the next occurrence (1 or 7 days after completion, even when done late or early); `"once"` tasks don't recur; completing twice doesn't duplicate; missed days don't pile up; next occurrences stay out of the plan until due.
- **Conflict detection**: same-pet and cross-pet overlaps, one task overlapping several, back-to-back tasks and untimed tasks not flagged, and overlaps that run past midnight.
- **Plan generation**: exact-fit time budget, zero minutes available, greedy skipping with reasons, tasks moved when their slot is taken or before the plan start, untimed tasks filling gaps only when they fit, and no overlapping entries (including across midnight).
- **Validation**: invalid priority, frequency, duration or time rejected; failed edits leave a task unchanged; unknown ids/pet names raise `KeyError`; duplicate pet names rejected.

Successful test run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/davidifeanyi/Projects/PawPal/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 37 items

tests/test_pawpal.py .....................................               [100%]

============================== 37 passed in 0.15s ==============================
```

**Confidence Level: ★★★★☆ (4/5)**

All 37 tests pass, covering the core scheduling logic and its edge cases, and writing them uncovered (and fixed) two real bugs: overlaps past midnight were missed, and a rejected edit left invalid values on a task. It isn't 5 stars because the tests exercise `pawpal_system.py` only. The Streamlit UI in `app.py` is untested, and the greedy planner is a deliberate simplification that can leave minutes unused rather than finding the best possible fit.

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
