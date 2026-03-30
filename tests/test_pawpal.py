from datetime import date, time, timedelta
from pawpal_system import Task, TaskOccurrence, Pet, Owner, Scheduler, RecurrenceRule


def test_task_occurrence_mark_complete():
    occ = TaskOccurrence(occurrence_id="o_test", task_id="t_test", date=date.today(), start_time=time(9, 0), end_time=time(9, 30))
    assert occ.status == "scheduled"
    occ.mark_complete()
    assert occ.status == "completed"


def test_pet_add_task_increases_count():
    pet = Pet(pet_id="p_test", name="Buddy")
    initial = len(pet.tasks)
    t = Task(task_id="t1", title="Feed", duration_minutes=5)
    pet.add_task(t)
    assert len(pet.tasks) == initial + 1
    assert pet.tasks[-1].task_id == "t1"


def test_sorting_correctness():
    sched = Scheduler()
    today = date.today()
    # earlier occurrence
    a = TaskOccurrence(occurrence_id="a", task_id="t_a", date=today, start_time=time(8, 0), end_time=time(8, 30), priority=1)
    # later occurrence
    b = TaskOccurrence(occurrence_id="b", task_id="t_b", date=today, start_time=time(9, 0), end_time=time(9, 30), priority=1)
    # same time but higher priority should come first
    c = TaskOccurrence(occurrence_id="c", task_id="t_c", date=today, start_time=time(9, 0), end_time=time(9, 20), priority=5)

    ordered = sched.sort_by_time([b, c, a])
    assert ordered[0].occurrence_id == "a"
    # c has same start as b but higher priority, so c before b
    assert ordered[1].occurrence_id == "c"
    assert ordered[2].occurrence_id == "b"


def test_recurrence_logic_creates_next_day_task():
    owner = Owner(owner_id="o1", name="Owner")
    pet = Pet(pet_id="p1", name="Rex")
    owner.add_pet(pet)

    # create a daily recurring task starting today
    rr = RecurrenceRule(freq="daily", interval=1)
    task = Task(task_id="rec1", title="Walk", duration_minutes=30, recurrence=rr)
    pet.add_task(task)

    # expand to get today's occurrence
    occs = task.to_occurrences(date.today(), date.today())
    assert occs, "expected an occurrence for today"
    occ = occs[0]

    sched = Scheduler()
    new_occ = sched.mark_occurrence_complete(owner, occ)

    # mark_occurrence_complete should return the next day's occurrence
    assert new_occ is not None
    assert new_occ.date == date.today() + timedelta(days=1)


def test_conflict_detection_flags_overlap():
    sched = Scheduler()
    d = date.today()
    o1 = TaskOccurrence(occurrence_id="x1", task_id="t1", date=d, start_time=time(10, 0), end_time=time(11, 0))
    o2 = TaskOccurrence(occurrence_id="x2", task_id="t2", date=d, start_time=time(10, 30), end_time=time(11, 30))
    conflicts = sched.detect_conflicts([o1, o2])
    assert len(conflicts) == 1
    a, b = conflicts[0]
    assert (a.occurrence_id, b.occurrence_id) in [("x1", "x2"), ("x2", "x1")]
