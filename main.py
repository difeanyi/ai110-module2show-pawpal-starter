"""Demo script: build an owner with two pets, add tasks, and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high", time="07:30", category="walk"))
    mochi.add_task(Task("Breakfast", duration_minutes=10, priority="high", time="08:15", category="feeding"))
    mochi.add_task(Task("Fetch in the yard", duration_minutes=45, priority="low", category="enrichment"))
    luna.add_task(Task("Thyroid meds", duration_minutes=5, priority="high", time="09:00", category="meds"))
    luna.add_task(Task("Clean litter box", duration_minutes=10, priority="medium", category="grooming"))
    luna.add_task(Task("Brush fur", duration_minutes=15, priority="low", time="18:00",
                       frequency="weekly", category="grooming"))

    scheduler = Scheduler(owner, start_time=time(7, 0))
    plan = scheduler.generate_plan(date.today())

    print("=" * 60)
    print(f"Today's Schedule for {owner.name}'s pets ({', '.join(p.name for p in owner.pets)})")
    print("=" * 60)
    print(plan.summary())


if __name__ == "__main__":
    main()
