"""Simple tests for the PawPal+ system.

Runnable two ways:
    pytest test/test_pawpal.py
    python test/test_pawpal.py
"""

import os
import sys
from datetime import date, datetime, timedelta

# Allow running directly (python test/test_pawpal.py) by putting the project
# root on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import (
    AnimalType,
    Calendar,
    CareNeed,
    CareType,
    Event,
    EventStatus,
    Pet,
    PetAttributes,
    Scheduler,
)


def make_pet() -> Pet:
    return Pet(
        id=1,
        name="Rex",
        animal=AnimalType.DOG,
        breed="Labrador",
        attributes=PetAttributes(),
    )


def test_task_completion() -> None:
    """Calling mark_complete() changes the task's status to completed."""
    task = CareNeed(id=1, type=CareType.WALK, frequency_per_day=1,
                    duration_minutes=30)
    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_task_addition() -> None:
    """Adding a task to a Pet increases that pet's task count."""
    pet = make_pet()
    assert len(pet.care_needs) == 0  # no tasks yet

    pet.add_care_need(
        CareNeed(id=1, type=CareType.FEED, frequency_per_day=2,
                 duration_minutes=15)
    )

    assert len(pet.care_needs) == 1


def test_sorting_chronological_order() -> None:
    """Sorting correctness: generated events come out in chronological order.

    A single need repeated several times a day is placed into successive free
    slots. The resulting events must be ordered by start time, each starting no
    earlier than the previous one ended.
    """
    pet = make_pet()
    pet.add_care_need(
        CareNeed(id=1, type=CareType.WALK, frequency_per_day=4,
                 duration_minutes=30)
    )
    calendar = Calendar(id=1)
    scheduler = Scheduler()

    events = scheduler.generate_schedule([pet], calendar, day=date(2026, 7, 6))

    assert len(events) == 4  # all four occurrences placed
    starts = [e.start for e in events]
    assert starts == sorted(starts)  # returned in chronological order
    # No two placements overlap: each starts at/after the previous one's end.
    for earlier, later in zip(events, events[1:]):
        assert later.start >= earlier.end


def test_recurrence_daily_occurs_every_day() -> None:
    """Recurrence logic: a completed daily need still occurs the next day.

    The system models recurrence via ``occurs_on(day)`` re-evaluated per day
    rather than by spawning a new task object. Marking today's need complete
    must not stop it from being scheduled tomorrow.
    """
    pet = make_pet()
    need = CareNeed(id=1, type=CareType.FEED, frequency_per_day=1,
                    duration_minutes=15)
    pet.add_care_need(need)

    today = date(2026, 7, 6)
    tomorrow = today + timedelta(days=1)

    # Daily need occurs on both days before completion.
    assert need.occurs_on(today) is True
    assert need.occurs_on(tomorrow) is True

    # Schedule and complete today's occurrence.
    scheduler = Scheduler()
    today_events = scheduler.generate_schedule([pet], Calendar(id=1), day=today)
    assert len(today_events) == 1
    need.mark_complete()

    # Recurrence still fires tomorrow: a fresh schedule places the need again.
    assert need.occurs_on(tomorrow) is True
    tomorrow_events = scheduler.generate_schedule(
        [pet], Calendar(id=2), day=tomorrow
    )
    assert len(tomorrow_events) == 1
    assert tomorrow_events[0].start.date() == tomorrow


def test_conflict_detection_flags_duplicate_times() -> None:
    """Conflict detection: two events at the same time are flagged as a conflict."""
    scheduler = Scheduler()
    start = datetime(2026, 7, 6, 8, 0)
    end = start + timedelta(minutes=30)

    # Two events for different pets occupying the exact same time window.
    first = Event(id=1, type=CareType.WALK, start=start, end=end,
                  status=EventStatus.SCHEDULED, pet_id=1, care_need_id=1)
    second = Event(id=2, type=CareType.FEED, start=start, end=end,
                   status=EventStatus.SCHEDULED, pet_id=2, care_need_id=2)

    conflicts = scheduler.detect_conflicts([first, second])

    assert len(conflicts) == 1
    assert conflicts[0].overlap_minutes == 30  # full 30-minute overlap

    # Sanity check the boundary: back-to-back events must NOT conflict.
    third = Event(id=3, type=CareType.PLAY, start=end,
                  end=end + timedelta(minutes=30),
                  status=EventStatus.SCHEDULED, pet_id=3, care_need_id=3)
    assert scheduler.detect_conflicts([first, third]) == []


if __name__ == "__main__":
    test_task_completion()
    test_task_addition()
    test_sorting_chronological_order()
    test_recurrence_daily_occurs_every_day()
    test_conflict_detection_flags_duplicate_times()
    print("All tests passed.")
