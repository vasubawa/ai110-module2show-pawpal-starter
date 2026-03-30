from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any


@dataclass
class RecurrenceRule:
    freq: Optional[str] = None
    interval: int = 1
    byweekday: Optional[List[int]] = None
    time_of_day: Optional[time] = None
    end_date: Optional[date] = None

    def next_dates(self, from_date: date, count: int = 1) -> List[date]:
        raise NotImplementedError

    def expand(self, start_date: date, end_date: date) -> List[date]:
        raise NotImplementedError


@dataclass
class Task:
    task_id: str
    title: str
    duration_minutes: int = 0
    priority: int = 0
    time_window_start: Optional[time] = None
    time_window_end: Optional[time] = None
    recurrence: Optional[RecurrenceRule] = None
    type: Optional[str] = None
    notes: Optional[str] = None

    def next_occurrence(self, from_date: date) -> Optional[date]:
        raise NotImplementedError

    def is_conflicting(self, other: "Task") -> bool:
        raise NotImplementedError

    def to_occurrences(self, start_date: date, end_date: date) -> List["TaskOccurrence"]:
        raise NotImplementedError


@dataclass
class TaskOccurrence:
    occurrence_id: str
    task_id: str
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: str = "scheduled"

    def overlaps(self, other: "TaskOccurrence") -> bool:
        raise NotImplementedError

    def mark_complete(self) -> None:
        self.status = "completed"

    def reschedule(self, new_start: time) -> None:
        raise NotImplementedError


@dataclass
class Pet:
    pet_id: str
    name: str
    species: Optional[str] = None
    age: Optional[int] = None
    owner_id: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def list_upcoming(self, days: int = 7) -> List[TaskOccurrence]:
        raise NotImplementedError


@dataclass
class Owner:
    owner_id: str
    name: str
    contact_info: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_tasks(self, day: date) -> List[TaskOccurrence]:
        raise NotImplementedError


@dataclass
class Availability:
    owner_id: str
    date: date
    time_windows: List[Dict[str, time]] = field(default_factory=list)

    def is_available(self, start: time, end: time) -> bool:
        raise NotImplementedError

    def add_block(self, start: time, end: time) -> None:
        self.time_windows.append({"start": start, "end": end})


@dataclass
class DailyPlan:
    date: date
    owner_id: str
    items: List[TaskOccurrence] = field(default_factory=list)
    explanations: Dict[str, str] = field(default_factory=dict)

    def to_list(self) -> List[TaskOccurrence]:
        return self.items

    def to_text(self) -> str:
        raise NotImplementedError

    def export_ical(self) -> str:
        raise NotImplementedError


@dataclass
class Notification:
    notification_id: str
    occurrence_id: str
    method: str
    time_before_minutes: int = 15
    sent: bool = False

    def schedule(self) -> None:
        raise NotImplementedError

    def send_now(self) -> None:
        raise NotImplementedError


class TaskManager:
    def __init__(self) -> None:
        self.tasks: Dict[str, Task] = {}

    def create_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def update_task(self, task_id: str, **changes) -> None:
        raise NotImplementedError

    def delete_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            del self.tasks[task_id]

    def get_tasks_for_owner_on_date(self, owner: Owner, day: date) -> List[TaskOccurrence]:
        raise NotImplementedError

    def expand_recurring(self, task: Task, start_date: date, end_date: date) -> List[TaskOccurrence]:
        raise NotImplementedError


class Scheduler:
    def __init__(self, max_daily_minutes: Optional[int] = None) -> None:
        self.max_daily_minutes = max_daily_minutes

    def generate_daily_plan(self, owner: Owner, day: date) -> DailyPlan:
        raise NotImplementedError

    def detect_conflicts(self, occurrences: List[TaskOccurrence]) -> List[tuple]:
        raise NotImplementedError

    def resolve_conflicts(self, occurrences: List[TaskOccurrence]) -> List[TaskOccurrence]:
        raise NotImplementedError

    def explain_plan(self, plan: DailyPlan) -> str:
        raise NotImplementedError


__all__ = [
    "Task",
    "TaskOccurrence",
    "Pet",
    "Owner",
    "TaskManager",
    "Scheduler",
    "RecurrenceRule",
    "Availability",
    "DailyPlan",
    "Notification",
]
