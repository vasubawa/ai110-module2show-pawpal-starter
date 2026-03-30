from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any, Tuple
import uuid


@dataclass
class RecurrenceRule:
    freq: Optional[str] = None
    interval: int = 1
    byweekday: Optional[List[int]] = None
    time_of_day: Optional[time] = None
    end_date: Optional[date] = None

    def next_dates(self, from_date: date, count: int = 1) -> List[date]:
        # Return the next `count` dates on or after `from_date`.
        window_end = from_date + timedelta(days=365)
        dates = self.expand(from_date, window_end)
        return dates[:count]

    def expand(self, start_date: date, end_date: date) -> List[date]:
        # Very small recurrence support: daily and weekly.
        if not self.freq:
            return []
        dates: List[date] = []
        if self.freq.lower() == "daily":
            current = start_date
            while current <= end_date:
                if self.end_date and current > self.end_date:
                    break
                dates.append(current)
                current = current + timedelta(days=self.interval)
        elif self.freq.lower() == "weekly":
            # byweekday: list of 0=Mon .. 6=Sun
            current = start_date
            while current <= end_date:
                if self.end_date and current > self.end_date:
                    break
                week_offset = (current - start_date).days // 7
                if (self.byweekday is None or current.weekday() in self.byweekday) and (week_offset % self.interval == 0):
                    dates.append(current)
                current = current + timedelta(days=1)
        else:
            # unsupported freq -> no expansion
            return []
        return dates


@dataclass
class Task:
    task_id: str
    title: str
    duration_minutes: int = 0
    priority: int = 0
    time_window_start: Optional[time] = None
    time_window_end: Optional[time] = None
    recurrence: Optional[RecurrenceRule] = None
    scheduled_date: Optional[date] = None
    type: Optional[str] = None
    notes: Optional[str] = None

    def next_occurrence(self, from_date: date) -> Optional[date]:
        # If the task has a specific scheduled date, return that if it's on/after from_date
        if self.scheduled_date and self.scheduled_date >= from_date:
            return self.scheduled_date
        if self.recurrence:
            dates = self.recurrence.next_dates(from_date, count=1)
            return dates[0] if dates else None
        return None

    def is_conflicting(self, other: "Task") -> bool:
        # Basic check: if both tasks have a scheduled_date and overlapping time windows on the same day
        if self.scheduled_date and other.scheduled_date and self.scheduled_date == other.scheduled_date:
            if self.time_window_start and self.time_window_end and other.time_window_start and other.time_window_end:
                return not (
                    self.time_window_end <= other.time_window_start or other.time_window_end <= self.time_window_start
                )
        return False

    def to_occurrences(self, start_date: date, end_date: date) -> List["TaskOccurrence"]:
        occs: List[TaskOccurrence] = []
        default_time = time(9, 0)

        def mk_occ(d: date, start_t: time) -> TaskOccurrence:
            st_dt = datetime.combine(d, start_t)
            en_dt = st_dt + timedelta(minutes=self.duration_minutes)
            return TaskOccurrence(
                occurrence_id=str(uuid.uuid4()),
                task_id=self.task_id,
                date=d,
                start_time=start_t,
                end_time=en_dt.time(),
            )

        # one-off scheduled date
        if self.scheduled_date:
            if start_date <= self.scheduled_date <= end_date:
                start_t = self.recurrence.time_of_day if (self.recurrence and self.recurrence.time_of_day) else (self.time_window_start or default_time)
                occs.append(mk_occ(self.scheduled_date, start_t))
            return occs

        # recurring
        if self.recurrence:
            dates = self.recurrence.expand(start_date, end_date)
            for d in dates:
                start_t = self.recurrence.time_of_day if self.recurrence.time_of_day else (self.time_window_start or default_time)
                occs.append(mk_occ(d, start_t))
            return occs

        # no recurrence and no scheduled date -> nothing to expand
        return []


@dataclass
class TaskOccurrence:
    occurrence_id: str
    task_id: str
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: str = "scheduled"
    # convenience fields filled by Pet/Owner when expanding
    pet_id: Optional[str] = None
    title: Optional[str] = None
    priority: int = 0

    def overlaps(self, other: "TaskOccurrence") -> bool:
        if self.date != other.date:
            return False
        if self.start_time is None or self.end_time is None or other.start_time is None or other.end_time is None:
            return False
        a_start = datetime.combine(self.date, self.start_time)
        a_end = datetime.combine(self.date, self.end_time)
        b_start = datetime.combine(other.date, other.start_time)
        b_end = datetime.combine(other.date, other.end_time)
        return a_start < b_end and b_start < a_end

    def mark_complete(self) -> None:
        self.status = "completed"

    def reschedule(self, new_start: time) -> None:
        if self.start_time and self.end_time:
            old_start = datetime.combine(self.date, self.start_time)
            old_end = datetime.combine(self.date, self.end_time)
            delta = old_end - old_start
            new_end = (datetime.combine(self.date, new_start) + delta).time()
            self.start_time = new_start
            self.end_time = new_end
        else:
            self.start_time = new_start


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
        start_date = date.today()
        return self.list_upcoming_from(start_date, days)

    def list_upcoming_from(self, start_date: date, days: int = 7) -> List[TaskOccurrence]:
        end_date = start_date + timedelta(days=days - 1)
        occs: List[TaskOccurrence] = []
        for task in self.tasks:
            for occ in task.to_occurrences(start_date, end_date):
                occ.pet_id = self.pet_id
                occ.title = task.title
                occ.priority = task.priority
                occs.append(occ)
        return occs


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
        occs: List[TaskOccurrence] = []
        for pet in self.pets:
            occs.extend(pet.list_upcoming_from(day, days=1))
        return occs


@dataclass
class Availability:
    owner_id: str
    date: date
    time_windows: List[Dict[str, time]] = field(default_factory=list)

    def is_available(self, start: time, end: time) -> bool:
        """Return True if the owner is available for the given start/end time."""
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
        """Return a human-readable text version of the daily plan."""
        raise NotImplementedError

    def export_ical(self) -> str:
        """Export the daily plan as an iCalendar string."""
        raise NotImplementedError


@dataclass
class Notification:
    notification_id: str
    occurrence_id: str
    method: str
    time_before_minutes: int = 15
    sent: bool = False

    def schedule(self) -> None:
        """Schedule the notification (placeholder; integrate with real notifier)."""
        raise NotImplementedError

    def send_now(self) -> None:
        """Send the notification immediately (placeholder)."""
        raise NotImplementedError


class TaskManager:
    def __init__(self) -> None:
        self.tasks: Dict[str, Task] = {}

    def create_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def update_task(self, task_id: str, **changes) -> None:
        """Update fields on an existing task using keyword args."""
        raise NotImplementedError

    def delete_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            del self.tasks[task_id]

    def get_tasks_for_owner_on_date(self, owner: Owner, day: date) -> List[TaskOccurrence]:
        return owner.get_tasks(day)

    def expand_recurring(self, task: Task, start_date: date, end_date: date) -> List[TaskOccurrence]:
        return task.to_occurrences(start_date, end_date)


class Scheduler:
    def __init__(self, max_daily_minutes: Optional[int] = None) -> None:
        self.max_daily_minutes = max_daily_minutes

    def generate_daily_plan(self, owner: Owner, day: date) -> DailyPlan:
        occurrences = owner.get_tasks(day)
        # sort by priority desc, then start_time asc
        def sort_key(o: TaskOccurrence) -> Tuple[int, time]:
            start = o.start_time or time(9, 0)
            return (-o.priority, start)

        occurrences = sorted(occurrences, key=sort_key)

        scheduled: List[TaskOccurrence] = []
        explanations: Dict[str, str] = {}

        for occ in occurrences:
            conflict = next((s for s in scheduled if s.overlaps(occ)), None)
            if not conflict:
                scheduled.append(occ)
                explanations[occ.occurrence_id] = f"Scheduled (priority {occ.priority})"
            else:
                # keep the higher-priority occurrence
                if occ.priority > conflict.priority:
                    # replace
                    scheduled = [s for s in scheduled if s != conflict]
                    explanations[occ.occurrence_id] = f"Scheduled (higher priority than {conflict.title or conflict.task_id})"
                    explanations[conflict.occurrence_id] = f"Skipped (conflict with higher-priority {occ.title or occ.task_id})"
                    scheduled.append(occ)
                else:
                    explanations[occ.occurrence_id] = f"Skipped (conflict with higher-priority {conflict.title or conflict.task_id})"

        plan = DailyPlan(date=day, owner_id=owner.owner_id, items=scheduled, explanations=explanations)
        return plan

    def detect_conflicts(self, occurrences: List[TaskOccurrence]) -> List[tuple]:
        conflicts: List[tuple] = []
        n = len(occurrences)
        for i in range(n):
            for j in range(i + 1, n):
                if occurrences[i].overlaps(occurrences[j]):
                    conflicts.append((occurrences[i], occurrences[j]))
        return conflicts

    def resolve_conflicts(self, occurrences: List[TaskOccurrence]) -> List[TaskOccurrence]:
        # Simple greedy resolution using priority then start time
        occurrences = sorted(occurrences, key=lambda o: (-o.priority, o.start_time or time(9, 0)))
        scheduled: List[TaskOccurrence] = []
        for occ in occurrences:
            if any(s.overlaps(occ) for s in scheduled):
                continue
            scheduled.append(occ)
        return scheduled

    def explain_plan(self, plan: DailyPlan) -> str:
        lines: List[str] = []
        for item in plan.items:
            title = item.title or item.task_id
            when = f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')}" if item.start_time and item.end_time else "time TBD"
            reason = plan.explanations.get(item.occurrence_id, "Scheduled")
            lines.append(f"{when}: {title} ({item.pet_id}) — {reason}")
        # include skipped/other explanations
        skipped = [v for k, v in plan.explanations.items() if k not in {i.occurrence_id for i in plan.items}]
        if skipped:
            lines.append("")
            lines.append("Notes:")
            for s in skipped:
                lines.append(f"- {s}")
        return "\n".join(lines)


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
