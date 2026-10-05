"""Demo script: add tasks out of order, show sorting/filtering, and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(title: str, pairs: list[tuple[Pet, Task]]) -> None:
    """Print a heading and one line per (pet, task) pair."""
    print(f"\n{title}")
    print("-" * len(title))
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        done = " [done]" if task.completed else ""
        if task.due_date:
            done += f" [due {task.due_date:%a %d %b}]"
        print(f"  {task.time or '--:--'}  {pet.name:<6} {task.description:<18} "
              f"{task.duration_minutes:>3} min  {task.priority:<6}{done}")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=120)

    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are added deliberately out of time order (and "9:00" is not zero-padded).
    luna.add_task(Task("Brush fur", duration_minutes=15, priority="low", time="18:00",
                       frequency="weekly", category="grooming"))
    mochi.add_task(Task("Breakfast", duration_minutes=10, priority="high", time="08:15", category="feeding"))
    mochi.add_task(Task("Fetch in the yard", duration_minutes=45, priority="low", category="enrichment"))
    luna.add_task(Task("Thyroid meds", duration_minutes=5, priority="high", time="9:00", category="meds"))
    mochi.add_task(Task("Evening walk", duration_minutes=25, priority="medium", time="17:30", category="walk"))
    luna.add_task(Task("Clean litter box", duration_minutes=10, priority="medium", category="grooming"))
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high", time="07:30", category="walk"))

    # Deliberate clashes for conflict detection:
    luna.add_task(Task("Breakfast", duration_minutes=5, priority="high", time="08:15", category="feeding"))  # same time as Mochi's breakfast
    mochi.add_task(Task("Ear drops", duration_minutes=5, priority="high", time="07:45", category="meds"))    # during Mochi's walk

    scheduler = Scheduler(owner, start_time=time(7, 0))
    today = date.today()
    # Thyroid meds (daily) already given -> a new instance is created for tomorrow.
    next_meds = scheduler.mark_task_complete("Luna", task_id=2, on=today)
    print(f"Completed Thyroid meds; next occurrence #{next_meds.task_id} due {next_meds.due_date:%a %d %b}")

    all_tasks = scheduler.get_tasks()
    print_tasks("Tasks as added (grouped by pet)", all_tasks)
    print_tasks("Sorted by time (sort_by_time)", scheduler.sort_by_time(all_tasks))
    print_tasks("Sorted by priority, then shortest (sort_tasks)", scheduler.sort_tasks(all_tasks))
    print_tasks("Mochi's tasks by time (filter + sort)",
                scheduler.sort_by_time(scheduler.filter_tasks(all_tasks, pet_name="Mochi")))
    print_tasks("Completed tasks", scheduler.get_tasks(completed=True))
    print_tasks("Still to do", scheduler.get_tasks(completed=False))

    print("\nConflict check (detect_conflicts)")
    print("---------------------------------")
    conflicts = scheduler.detect_conflicts(on=today)
    for warning in conflicts:
        print(f"  WARNING: {warning}")
    if not conflicts:
        print("  No conflicts found.")

    plan = scheduler.generate_plan(today)
    print()
    print("=" * 60)
    print(f"Today's Schedule for {owner.name}'s pets ({', '.join(p.name for p in owner.pets)})")
    print("=" * 60)
    print(plan.summary())


if __name__ == "__main__":
    main()
