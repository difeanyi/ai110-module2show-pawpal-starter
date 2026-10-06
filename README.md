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

## ✨ Features

**Pets and tasks**
- **Multiple pets per owner.** Pet names must be unique, and every task belongs to a pet.
- **Validated tasks.** Each task has a duration, a priority (low / medium / high), an optional preferred start time and a frequency (once / daily / weekly). Invalid values are rejected when the task is created, and times like `9:00` are stored as `09:00`.
- **Automatic task IDs.** Each pet gives its tasks unique IDs, so they can be edited, completed or removed reliably.

**Organizing tasks**
- **Sorting by time.** Tasks are ordered by their preferred start time, compared as real clock times rather than text, so `9:00` comes before `10:00`. Tasks with no set time go last.
- **Sorting by priority.** High-priority tasks come first. Within the same priority, shorter tasks come first so more of them fit in the day.
- **Filtering by pet and status.** Show one pet's tasks, only open or only completed tasks, or only what's due today. Filters and sorts can be combined.

**Building the daily plan**
- **Time-budget planning.** Tasks are chosen greedily in priority order and kept only if they fit in the owner's remaining minutes. High-priority care is never dropped to make room for lower-priority tasks.
- **Preferred-time placement.** Tasks with a preferred time are scheduled at that time. Tasks without one fill the gaps before and between them, and only if they finish in time. The final plan never has overlapping tasks.
- **Explained decisions.** Every scheduled task shows why it was included (for example "high priority, preferred 08:15"), and every skipped task shows why it was left out (for example "needs 45 min but only 20 min left").

**Conflicts and recurrence**
- **Conflict warnings.** The app detects tasks whose time slots overlap, for the same pet or for different pets, and shows a warning instead of crashing. A task that starts exactly when another ends is not a conflict. When the plan is built, the later task in each clashing pair is moved to the next free slot.
- **Daily and weekly recurrence.** Marking a daily or weekly task complete keeps it as history and automatically creates the next occurrence, due 1 or 7 days after the day it was completed. One-off tasks don't repeat, and completing the same task twice never creates a duplicate.
- **Due-date awareness.** Future occurrences stay out of today's plan until their due date arrives.

**Interfaces**
- **Streamlit app** (`streamlit run app.py`). Add pets and tasks, filter and sort the task list, see conflict warnings before planning, mark tasks complete, and generate a schedule with a summary of time used and tasks skipped.
- **CLI demo** (`python main.py`). Prints sorted and filtered task lists, a conflict check and today's schedule.
- **Automated tests** (`pytest`). 14 tests cover task completion, adding tasks, filtering, recurrence and conflict detection.

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

### Main UI features

Run `streamlit run app.py`. The page is split into four areas, top to bottom:

| Area | What you can do |
|------|-----------------|
| **Owner** | Set the owner's name and how many minutes they have for pet care today. This is the time budget the scheduler works within. |
| **Pets** | Add a pet with a name, species, breed and age. Adding a second pet with the same name shows an error instead of creating a duplicate. |
| **Tasks** | Add a task for a chosen pet with a duration, priority, frequency (daily / weekly / once) and an optional preferred start time. Mark any open task complete. View the task list with **Show pet**, **Show** (Due today / Open / Completed / All) and **Sort by** (Time / Priority) controls. A live conflict check runs under the list. |
| **Build Schedule** | Pick when the day starts and click **Generate schedule** to see minutes used, tasks scheduled and skipped, the timed plan with a reason for each task, a table of skipped tasks, and a plain-text summary. |

The owner and all pets and tasks are kept in `st.session_state`, so nothing is lost when the page reruns after a click.

### Example workflow

1. **Set the time budget.** In **Owner**, enter `Jordan` and set **Minutes available today** to `90`.
2. **Add two pets.** In **Pets**, add `Mochi` (dog), then `Luna` (cat). Both appear in the pets table.
3. **Schedule some tasks.**
   - For Mochi: `Morning walk`, 30 min, high, daily, preferred start `08:00`.
   - For Luna: `Breakfast`, 5 min, high, daily, preferred start `08:00`.
   - For Mochi: `Brush fur`, 20 min, low, weekly, no preferred time.
4. **Review the task list.** With **Sort by: Time**, the two 08:00 tasks come first and the untimed brushing comes last. Switch to **Sort by: Priority** to see high-priority tasks first, or set **Show pet: Luna** to see only Luna's task.
5. **Notice the conflict warning.** Under the list, a yellow box reports that Mochi's walk (08:00–08:30) overlaps Luna's breakfast (08:00–08:05), between different pets.
6. **Generate today's schedule.** In **Build Schedule**, keep the start at 08:00 and click **Generate schedule**. Both 08:00 tasks are high priority, so the shorter one goes first. Luna's breakfast runs 08:00–08:05, Mochi's walk is moved to 08:05–08:35 (the reason says "moved to 08:05"), and the untimed brushing fills the next free slot at 08:35–08:55. The metrics show 55 / 90 minutes used.
7. **Complete a recurring task.** In **Tasks**, choose *Mochi: Morning walk* and click **Mark complete**. The app confirms "Next 'Morning walk' is due" tomorrow. Set **Show: All** to see both the completed walk and the new copy due tomorrow. The new copy stays out of the "Due today" view and today's plan until tomorrow.

### Key Scheduler behaviors shown

- **Sorting by time** (`sort_by_time`): chronological order across all pets, with untimed tasks last. `9:00` correctly sorts before `10:00`.
- **Sorting by priority** (`sort_tasks`): high → low, and shortest first within the same priority.
- **Filtering** (`filter_tasks`, `get_tasks`, `get_due_tasks`): by pet, by completion status, or by what's due today.
- **Conflict warnings** (`detect_conflicts`): overlapping time slots are reported for the same pet or different pets, as warnings rather than errors. The generated plan moves the later task so nothing overlaps.
- **Time budget** (`generate_plan`): tasks that don't fit in the remaining minutes are skipped with a reason, such as "needs 45 min but only 20 min left".
- **Daily and weekly recurrence** (`mark_task_complete` → `complete_task` → `next_occurrence`): completing a repeating task creates the next one with a due date.

### Sample CLI output

Running `python main.py` sets up Jordan with Mochi and Luna, adds ten tasks out of order (including two deliberate clashes), marks Luna's thyroid meds complete, and prints sorted lists, a conflict check and the schedule. Abridged output:

```
Completed Thyroid meds; next occurrence #5 due Wed 07 Oct

Sorted by time (sort_by_time)
-----------------------------
  07:30  Mochi  Morning walk        30 min  high
  07:45  Mochi  Ear drops            5 min  high
  08:15  Mochi  Breakfast           10 min  high
  08:15  Luna   Breakfast            5 min  high
  09:00  Luna   Thyroid meds         5 min  high   [done]
  09:00  Luna   Thyroid meds         5 min  high   [due Wed 07 Oct]
  17:30  Mochi  Evening walk        25 min  medium
  18:00  Luna   Brush fur           15 min  low
  --:--  Mochi  Fetch in the yard   45 min  low
  --:--  Luna   Clean litter box    10 min  medium

Mochi's tasks by time (filter + sort)
-------------------------------------
  07:30  Mochi  Morning walk        30 min  high
  07:45  Mochi  Ear drops            5 min  high
  08:15  Mochi  Breakfast           10 min  high
  17:30  Mochi  Evening walk        25 min  medium
  --:--  Mochi  Fetch in the yard   45 min  low

Conflict check (detect_conflicts)
---------------------------------
  WARNING: Mochi: Morning walk (07:30-08:00) overlaps Mochi: Ear drops (07:45-07:50) - same pet (Mochi)
  WARNING: Mochi: Breakfast (08:15-08:25) overlaps Luna: Breakfast (08:15-08:20) - different pets (Mochi & Luna)

============================================================
Today's Schedule for Jordan's pets (Mochi, Luna)
============================================================
Plan for Tuesday 06 Oct 2026 (100/120 min used)
  WARNING: Mochi: Morning walk (07:30-08:00) overlaps Mochi: Ear drops (07:45-07:50) - same pet (Mochi) - later task moved
  WARNING: Luna: Breakfast (08:15-08:20) overlaps Mochi: Breakfast (08:15-08:25) - different pets (Luna & Mochi) - later task moved
  07:00-07:10  Luna: Clean litter box (10 min, medium) - medium priority
  07:30-08:00  Mochi: Morning walk (30 min, high) - high priority, preferred 07:30
  08:00-08:05  Mochi: Ear drops (5 min, high) - high priority, preferred 07:45 (moved to 08:00: slot taken or before plan start)
  08:15-08:20  Luna: Breakfast (5 min, high) - high priority, preferred 08:15
  08:20-08:30  Mochi: Breakfast (10 min, high) - high priority, preferred 08:15 (moved to 08:20: slot taken or before plan start)
  17:30-17:55  Mochi: Evening walk (25 min, medium) - medium priority, preferred 17:30
  18:00-18:15  Luna: Brush fur (15 min, low) - low priority, preferred 18:00
Skipped:
  Mochi: Fetch in the yard - needs 45 min but only 20 min left
```

The full output also lists the tasks in the order they were added, sorted by priority, and split into completed and still to do.
