from datetime import date, time
from pawpal_system import Task, TaskOccurrence, Pet


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
