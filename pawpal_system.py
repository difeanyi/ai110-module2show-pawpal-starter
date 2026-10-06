"""PawPal+ core system: owners, pets, care tasks, and daily scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import date, datetime, time, timedelta

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")
RECURRENCE = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def parse_time(value: str) -> time:
    """Parse an "HH:MM" string into a time object."""
    return datetime.strptime(value, "%H:%M").time()


def add_minutes(start: time, minutes: int) -> time:
    """Return the clock time `minutes` after `start`."""
    return (datetime.combine(date.min, start) + timedelta(minutes=minutes)).time()


def to_minutes(t: time) -> int:
    """Return minutes since midnight, so times can be compared without wrapping at 00:00."""
    return t.hour * 60 + t.minute


def from_minutes(minutes: int) -> time:
    """Return the clock time for a minutes-since-midnight count (wraps past 24:00 for display)."""
    return add_minutes(time.min, minutes)


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, enrichment)."""

    description: str
    duration_minutes: int = 15
    priority: str = "medium"  # "low" | "medium" | "high"
    time: str | None = None  # preferred start, "HH:MM"
    frequency: str = "daily"  # "once" | "daily" | "weekly"
    category: str = "general"
    completed: bool = False
    last_completed: date | None = None
    due_date: date | None = None  # None = due now
    task_id: int = 0  # assigned by Pet.add_task

    def __post_init__(self) -> None:
        """Validate fields so bad input fails early instead of breaking the scheduler."""
        if self.priority not in PRIORITY_SCORES:
            raise ValueError(f"priority must be one of {list(PRIORITY_SCORES)}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.time is not None:
            self.time = parse_time(self.time).strftime("%H:%M")  # validate and zero-pad, e.g. "9:00" -> "09:00"

    def mark_complete(self, on: date | None = None) -> None:
        """Mark this task as done on the given day (defaults to today)."""
        self.completed = True
        self.last_completed = on or date.today()

    def update(self, **changes) -> None:
        """Update one or more fields of this task, re-validating afterwards."""
        valid = {f.name for f in fields(self)} - {"task_id"}
        unknown = set(changes) - valid
        if unknown:
            raise AttributeError(f"Task has no editable field(s): {sorted(unknown)}")
        updated = replace(self, **changes)  # validates in __post_init__ before self is touched
        for f in fields(self):
            setattr(self, f.name, getattr(updated, f.name))

    def priority_score(self) -> int:
        """Convert priority into a number used for sorting (higher = more important)."""
        return PRIORITY_SCORES[self.priority]

    def preferred_start(self) -> time | None:
        """Return the preferred start time as a time object, if one is set."""
        return parse_time(self.time) if self.time else None

    def is_due(self, on: date | None = None) -> bool:
        """Return True if this task is not done and its due date has arrived (or passed).

        Args:
            on: The day to check. Defaults to today.

        Returns:
            False if the task is completed or its due_date is after `on`; True otherwise.
            A task with no due_date is treated as due immediately.
        """
        on = on or date.today()
        return not self.completed and (self.due_date is None or self.due_date <= on)

    def next_occurrence(self, completed_on: date | None = None) -> Task | None:
        """Return a fresh copy of a daily/weekly task due one period after completed_on, or None for "once".

        The copy keeps every detail (description, duration, priority, time, category)
        but resets completed/last_completed and task_id (the Pet assigns a new id).
        The next due date counts from the completion day, not the old due date, so a
        weekly task finished two days late is next due seven days after it was finished.

        Args:
            completed_on: The day the task was completed. Defaults to today.

        Returns:
            A new, uncompleted Task with due_date = completed_on + 1 day (daily) or
            + 7 days (weekly), or None if the task's frequency is "once".
        """
        if self.frequency not in RECURRENCE:
            return None
        completed_on = completed_on or date.today()
        return replace(self, completed=False, last_completed=None, task_id=0,
                       due_date=completed_on + RECURRENCE[self.frequency])


@dataclass
class Pet:
    """An animal being cared for, along with its care tasks."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> Task:
        """Add a care task for this pet, assigning it a unique id."""
        task.task_id = max((t.task_id for t in self.tasks), default=0) + 1
        self.tasks.append(task)
        return task

    def get_task(self, task_id: int) -> Task:
        """Return the task with the given id, or raise KeyError."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"{self.name} has no task with id {task_id}")

    def edit_task(self, task_id: int, **changes) -> Task:
        """Edit an existing task by its id."""
        task = self.get_task(task_id)
        task.update(**changes)
        return task

    def complete_task(self, task_id: int, on: date | None = None) -> Task | None:
        """Mark a task complete and, if it recurs, add its next occurrence; returns the new task or None.

        The completed task stays in the list as history. Calling this on a task that
        is already completed does nothing, so double-clicks can't create duplicates.

        Args:
            task_id: Id of the task to complete.
            on: The day it was completed. Defaults to today.

        Returns:
            The newly added next occurrence, or None if the task doesn't recur or was
            already completed.

        Raises:
            KeyError: If this pet has no task with that id.
        """
        task = self.get_task(task_id)
        if task.completed:
            return None  # already done; don't create a duplicate next occurrence
        on = on or date.today()
        task.mark_complete(on)
        next_task = task.next_occurrence(on)
        return self.add_task(next_task) if next_task else None

    def remove_task(self, task_id: int) -> None:
        """Remove a task by its id."""
        self.tasks.remove(self.get_task(task_id))

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """The pet owner, their daily time budget, and preferences."""

    name: str
    available_minutes: int
    preferences: dict[str, str] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner. Pet names must be unique per owner."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet:
        """Return the pet with the given name, or raise KeyError."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        raise KeyError(f"{self.name} has no pet named {name!r}")

    def remove_pet(self, name: str) -> None:
        """Remove a pet (and its tasks) by name."""
        self.pets.remove(self.get_pet(name))

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def update_available_time(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes = minutes

    def set_preference(self, key: str, value: str) -> None:
        """Set an owner preference (e.g. walk_time="morning")."""
        self.preferences[key] = value


@dataclass
class ScheduledTask:
    """One entry in a DailyPlan: which pet, which task, when, and why."""

    pet_name: str
    task: Task
    start: time
    end: time
    reason: str


@dataclass
class SkippedTask:
    """A task left out of the plan, and why."""

    pet_name: str
    task: Task
    reason: str


@dataclass
class DailyPlan:
    """The generated schedule for one day, with reasoning for each decision."""

    date: date
    available_minutes: int
    entries: list[ScheduledTask] = field(default_factory=list)
    skipped: list[SkippedTask] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total minutes of care scheduled."""
        return sum(e.task.duration_minutes for e in self.entries)

    def add_entry(self, pet_name: str, task: Task, start: time, reason: str) -> ScheduledTask:
        """Add a task to the schedule at the given start time."""
        entry = ScheduledTask(pet_name, task, start, add_minutes(start, task.duration_minutes), reason)
        self.entries.append(entry)
        return entry

    def add_skipped(self, pet_name: str, task: Task, reason: str) -> None:
        """Record a task that could not be scheduled and why."""
        self.skipped.append(SkippedTask(pet_name, task, reason))

    def summary(self) -> str:
        """Return a readable text version of the plan for the CLI or UI."""
        lines = [f"Plan for {self.date:%A %d %b %Y} "
                 f"({self.total_minutes}/{self.available_minutes} min used)"]
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        if not self.entries:
            lines.append("  Nothing scheduled.")
        for e in self.entries:
            lines.append(f"  {e.start:%H:%M}-{e.end:%H:%M}  {e.pet_name}: {e.task.description} "
                         f"({e.task.duration_minutes} min, {e.task.priority}) - {e.reason}")
        if self.skipped:
            lines.append("Skipped:")
            for s in self.skipped:
                lines.append(f"  {s.pet_name}: {s.task.description} - {s.reason}")
        return "\n".join(lines)


class Scheduler:
    """The "brain": retrieves, organizes and schedules tasks across all of an owner's pets."""

    def __init__(self, owner: Owner, start_time: time = time(8, 0)) -> None:
        """Create a scheduler for an owner, with plans starting at start_time."""
        self.owner = owner
        self.start_time = start_time

    # --- Retrieving ---------------------------------------------------------

    def get_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[tuple[Pet, Task]]:
        """Return all of the owner's (pet, task) pairs, optionally filtered by pet and/or completion status."""
        return self.filter_tasks(self.owner.get_all_tasks(), pet_name=pet_name, completed=completed)

    def filter_tasks(self, pairs: list[tuple[Pet, Task]], pet_name: str | None = None,
                     completed: bool | None = None) -> list[tuple[Pet, Task]]:
        """Keep only pairs matching the given pet name and/or completion status (None = don't filter).

        Works on any list of (pet, task) pairs, so it can be chained with the sort
        methods, e.g. sort_by_time(filter_tasks(pairs, pet_name="Mochi")).

        Args:
            pairs: The (pet, task) pairs to filter.
            pet_name: Keep only this pet's tasks. None keeps all pets.
            completed: True keeps only completed tasks, False only open ones, None both.

        Returns:
            A new list with the matching pairs, in their original order.
        """
        return [(p, t) for p, t in pairs
                if (pet_name is None or p.name == pet_name)
                and (completed is None or t.completed == completed)]

    def get_due_tasks(self, on: date | None = None) -> list[tuple[Pet, Task]]:
        """Return tasks that still need doing on the given day."""
        return [(p, t) for p, t in self.owner.get_all_tasks() if t.is_due(on)]

    # --- Organizing ---------------------------------------------------------

    def sort_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by priority (high first), then shortest first.

        The sort key is (-priority_score, duration_minutes): negating the score puts
        high priority first, and among equal priorities shorter tasks come first so
        more tasks fit into the time budget. Python's sort is stable, so ties keep
        their original order.

        Args:
            pairs: The (pet, task) pairs to sort.

        Returns:
            A new sorted list; the input is not modified.
        """
        return sorted(pairs, key=lambda pt: (-pt[1].priority_score(), pt[1].duration_minutes))

    def sort_by_time(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by preferred start time; tasks without a time go last.

        The sort key is (has_no_time, start_time). False sorts before True, so timed
        tasks come first, ordered by real time objects rather than "HH:MM" strings
        (string order would put "9:00" after "10:00"). Untimed tasks use time.min as
        a placeholder so None is never compared.

        Args:
            pairs: The (pet, task) pairs to sort.

        Returns:
            A new sorted list; the input is not modified.
        """
        return sorted(pairs, key=lambda pt: (pt[1].time is None, pt[1].preferred_start() or time.min))

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task fits in the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    def detect_conflicts(self, pairs: list[tuple[Pet, Task]] | None = None,
                         on: date | None = None) -> list[str]:
        """Return a warning for each pair of tasks whose preferred time slots overlap (never raises).

        Algorithm: keep only tasks with a preferred time, sort them by start, then
        compare each task with the ones after it. Two slots overlap when the later
        one starts before the earlier one ends. Because the list is sorted, the inner
        loop stops as soon as a task starts at or after the current one ends.
        Back-to-back tasks (one ends 08:00, next starts 08:00) are not conflicts.
        Clashes are reported for the same pet and for different pets, since one
        owner can't do two things at once either way.

        Args:
            pairs: The (pet, task) pairs to check. Defaults to the tasks due on `on`.
            on: The day to check when `pairs` is not given. Defaults to today.

        Returns:
            One human-readable warning string per overlapping pair; empty if none.
        """
        if pairs is None:
            pairs = self.get_due_tasks(on)
        # Only tasks with a preferred time can clash; sort by start so we can stop scanning early.
        timed = self.sort_by_time([pt for pt in pairs if pt[1].time])
        warnings = []
        for i, (pet_a, a) in enumerate(timed):
            a_start = a.preferred_start()
            a_end = to_minutes(a_start) + a.duration_minutes  # may exceed 24:00; compared as minutes, not wrapped
            for pet_b, b in timed[i + 1:]:
                b_start = b.preferred_start()
                if to_minutes(b_start) >= a_end:
                    break  # sorted by start, so no later task can overlap `a`
                who = f"same pet ({pet_a.name})" if pet_a is pet_b else f"different pets ({pet_a.name} & {pet_b.name})"
                warnings.append(
                    f"{pet_a.name}: {a.description} ({a.time}-{from_minutes(a_end):%H:%M}) overlaps "
                    f"{pet_b.name}: {b.description} ({b.time}-{add_minutes(b_start, b.duration_minutes):%H:%M}) "
                    f"- {who}"
                )
        return warnings

    # --- Managing -----------------------------------------------------------

    def mark_task_complete(self, pet_name: str, task_id: int, on: date | None = None) -> Task | None:
        """Mark one pet's task complete; returns the next occurrence if the task recurs."""
        return self.owner.get_pet(pet_name).complete_task(task_id, on)

    # --- Planning -----------------------------------------------------------

    def generate_plan(self, on: date | None = None) -> DailyPlan:
        """Choose due tasks that fit the owner's time budget and place them on a timeline.

        1. Choose (greedy): go through due tasks in sort_tasks order and keep each one
           that fits in the remaining minutes; the rest are recorded as skipped with a
           reason. Choices are never revisited, so leftover minutes may go unused.
        2. Warn: run detect_conflicts on the chosen tasks and store the messages.
        3. Place: timed tasks go at their preferred time, or as soon after as possible
           if the slot is taken or before start_time. Untimed tasks fill the gaps
           before each timed task (only if they finish in time), and any left over go
           after the last timed task. The result never has overlapping entries.

        Args:
            on: The day to plan. Defaults to today.

        Returns:
            A DailyPlan with entries, skipped tasks, conflict warnings and a reason
            for every decision.
        """
        on = on or date.today()
        plan = DailyPlan(date=on, available_minutes=self.owner.available_minutes)

        # 1. Choose: take due tasks in priority order and keep each one that fits (greedy).
        remaining = self.owner.available_minutes
        chosen: list[tuple[Pet, Task]] = []
        for pet, task in self.sort_tasks(self.get_due_tasks(on)):
            if self.fits_in_time(task, remaining):
                chosen.append((pet, task))
                remaining -= task.duration_minutes
            else:
                plan.add_skipped(pet.name, task,
                                 f"needs {task.duration_minutes} min but only {remaining} min left")

        # Warn about clashing preferred times; placement below resolves them by shifting later.
        plan.warnings = [w + " - later task moved" for w in self.detect_conflicts(chosen)]

        # 2. Place: timed tasks at their preferred time, untimed tasks fill the gaps.
        timed = self.sort_by_time([pt for pt in chosen if pt[1].time])
        untimed = [pt for pt in chosen if not pt[1].time]  # already in priority order
        # Track the cursor as minutes since midnight so it keeps increasing past 24:00 instead of wrapping.
        cursor = to_minutes(self.start_time)

        def place_untimed(pet: Pet, task: Task) -> None:
            """Schedule an untimed task at the cursor and advance the cursor."""
            nonlocal cursor
            plan.add_entry(pet.name, task, from_minutes(cursor), f"{task.priority} priority")
            cursor += task.duration_minutes

        for pet, task in timed:
            preferred = to_minutes(task.preferred_start())
            # Fill the gap before this timed task with untimed tasks that finish in time.
            while untimed and cursor + untimed[0][1].duration_minutes <= preferred:
                place_untimed(*untimed.pop(0))
            start = max(cursor, preferred)
            reason = f"{task.priority} priority, preferred {task.time}"
            if start > preferred:
                reason += f" (moved to {from_minutes(start):%H:%M}: slot taken or before plan start)"
            plan.add_entry(pet.name, task, from_minutes(start), reason)
            cursor = start + task.duration_minutes

        for pet, task in untimed:
            place_untimed(pet, task)

        return plan
