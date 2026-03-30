from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    today = date.today()

    owner = Owner(owner_id="o1", name="Alex")

    pet1 = Pet(pet_id="p1", name="Fido", species="dog", owner_id=owner.owner_id)
    pet2 = Pet(pet_id="p2", name="Mittens", species="cat", owner_id=owner.owner_id)
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # Tasks scheduled for today (some overlap to demonstrate conflict resolution)
    t1 = Task(task_id="t1", title="Morning Walk", duration_minutes=30, priority=5, scheduled_date=today, time_window_start=time(8, 0))
    t2 = Task(task_id="t2", title="Breakfast", duration_minutes=15, priority=3, scheduled_date=today, time_window_start=time(8, 15))
    t3 = Task(task_id="t3", title="Medication", duration_minutes=5, priority=9, scheduled_date=today, time_window_start=time(8, 10))

    pet1.add_task(t1)
    pet1.add_task(t2)
    pet2.add_task(t3)

    scheduler = Scheduler()
    # generate and print the scheduled plan (uses conflict resolution)
    plan = scheduler.generate_daily_plan(owner, today)
    print(f"Today's Schedule for {owner.name} ({today}):\n")
    print(scheduler.explain_plan(plan))

    # Demonstrate sorting of all occurrences (may include skipped/conflicted items)
    all_occs = owner.get_tasks(today)
    print("\nAll occurrences (original order):")
    for o in all_occs:
        print(f" - {o.start_time} {o.title} ({o.pet_id}) priority={o.priority}")

    sorted_occs = scheduler.sort_by_time(all_occs)
    print("\nAll occurrences (sorted by time, tie-break priority):")
    for o in sorted_occs:
        print(f" - {o.start_time} {o.title} ({o.pet_id}) priority={o.priority}")

    # Demonstrate filtering by pet name
    mittens_occs = owner.get_tasks(today, pet_names=["Mittens"])
    print("\nOccurrences for Mittens:")
    for o in mittens_occs:
        print(f" - {o.start_time} {o.title} ({o.pet_id}) status={o.status}")


if __name__ == "__main__":
    main()
