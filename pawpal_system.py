"""PawPal+ core system: owners, pets, care tasks, and daily scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, enrichment)."""

    task_id: int
    title: str
    category: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    preferred_time: str | None = None  # e.g. "morning", "evening"
    frequency: str = "daily"  # "daily" | "weekly"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def update(self, **changes) -> None:
        """Update one or more fields of this task."""
        pass

    def priority_score(self) -> int:
        """Convert priority into a number used for sorting."""
        pass


@dataclass
class Pet:
    """An animal being cared for, along with its care tasks."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def edit_task(self, task_id: int, **changes) -> None:
        """Edit an existing task by its id."""
        pass

    def remove_task(self, task_id: int) -> None:
        """Remove a task by its id."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass


@dataclass
class Owner:
    """The pet owner, their daily time budget, and preferences."""

    name: str
    available_minutes: int
    preferences: dict[str, str] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass

    def update_available_time(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        pass

    def set_preference(self, key: str, value: str) -> None:
        """Set an owner preference (e.g. walk_time="morning")."""
        pass


@dataclass
class DailyPlan:
    """The generated schedule for one day, with reasoning for each decision."""

    date: date
    scheduled_tasks: list[tuple[time, Task]] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_minutes: int = 0
    reasons: dict[int, str] = field(default_factory=dict)  # task_id -> reason

    def add_entry(self, task: Task, start_time: time, reason: str) -> None:
        """Add a task to the schedule at the given start time."""
        pass

    def add_skipped(self, task: Task, reason: str) -> None:
        """Record a task that could not be scheduled and why."""
        pass

    def summary(self) -> str:
        """Return a readable text version of the plan for the UI."""
        pass


class Scheduler:
    """Builds a DailyPlan for a pet based on the owner's constraints."""

    def __init__(self, owner: Owner, pet: Pet, start_time: time = time(8, 0)) -> None:
        self.owner = owner
        self.pet = pet
        self.start_time = start_time

    def sort_tasks(self) -> list[Task]:
        """Return tasks ordered by priority, then duration."""
        pass

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task fits in the remaining time budget."""
        pass

    def generate_plan(self) -> DailyPlan:
        """Build and return today's plan."""
        pass

    def explain_choice(self, task: Task) -> str:
        """Explain why a task was scheduled or skipped."""
        pass
