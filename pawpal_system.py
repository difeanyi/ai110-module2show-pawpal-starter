"""PawPal+ core system: owners, pets, care tasks, and daily scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date, datetime, time, timedelta

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


def parse_time(value: str) -> time:
    """Parse an "HH:MM" string into a time object."""
    return datetime.strptime(value, "%H:%M").time()


def add_minutes(start: time, minutes: int) -> time:
    """Return the clock time `minutes` after `start`."""
    return (datetime.combine(date.min, start) + timedelta(minutes=minutes)).time()


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
            parse_time(self.time)  # raises ValueError if not "HH:MM"

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
        for name, value in changes.items():
            setattr(self, name, value)
        self.__post_init__()

    def priority_score(self) -> int:
        """Convert priority into a number used for sorting (higher = more important)."""
        return PRIORITY_SCORES[self.priority]

    def preferred_start(self) -> time | None:
        """Return the preferred start time as a time object, if one is set."""
        return parse_time(self.time) if self.time else None

    def is_due(self, on: date | None = None) -> bool:
        """Return True if this task still needs doing on the given day."""
        on = on or date.today()
        if self.frequency == "once":
            return not self.completed
        if self.last_completed is None:
            return True
        if self.frequency == "daily":
            return self.last_completed < on
        return (on - self.last_completed).days >= 7  # weekly


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
        """Return (pet, task) pairs, optionally filtered by pet and/or completion status."""
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.completed == completed]
        return pairs

    def get_due_tasks(self, on: date | None = None) -> list[tuple[Pet, Task]]:
        """Return tasks that still need doing on the given day."""
        return [(p, t) for p, t in self.owner.get_all_tasks() if t.is_due(on)]

    # --- Organizing ---------------------------------------------------------

    def sort_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by priority (high first), then shortest first."""
        return sorted(pairs, key=lambda pt: (-pt[1].priority_score(), pt[1].duration_minutes))

    def sort_by_time(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by preferred start time; tasks without a time go last."""
        return sorted(pairs, key=lambda pt: (pt[1].time is None, pt[1].time or ""))

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task fits in the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    # --- Managing -----------------------------------------------------------

    def mark_task_complete(self, pet_name: str, task_id: int, on: date | None = None) -> Task:
        """Mark one pet's task as complete."""
        task = self.owner.get_pet(pet_name).get_task(task_id)
        task.mark_complete(on)
        return task

    # --- Planning -----------------------------------------------------------

    def generate_plan(self, on: date | None = None) -> DailyPlan:
        """Choose due tasks that fit the owner's time budget and place them on a timeline."""
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

        # 2. Place: timed tasks at their preferred time, untimed tasks fill the gaps.
        timed = self.sort_by_time([pt for pt in chosen if pt[1].time])
        untimed = [pt for pt in chosen if not pt[1].time]  # already in priority order
        cursor = self.start_time

        def place_untimed(pet: Pet, task: Task) -> None:
            """Schedule an untimed task at the cursor and advance the cursor."""
            nonlocal cursor
            plan.add_entry(pet.name, task, cursor, f"{task.priority} priority")
            cursor = add_minutes(cursor, task.duration_minutes)

        for pet, task in timed:
            preferred = task.preferred_start()
            # Fill the gap before this timed task with untimed tasks that finish in time.
            while untimed and add_minutes(cursor, untimed[0][1].duration_minutes) <= preferred:
                place_untimed(*untimed.pop(0))
            start = max(cursor, preferred)
            reason = f"{task.priority} priority, preferred {task.time}"
            if start > preferred:
                reason += f" (moved to {start:%H:%M}: slot taken or before plan start)"
            plan.add_entry(pet.name, task, start, reason)
            cursor = add_minutes(start, task.duration_minutes)

        for pet, task in untimed:
            place_untimed(pet, task)

        return plan
