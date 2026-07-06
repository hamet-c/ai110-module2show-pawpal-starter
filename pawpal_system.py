"""PawPal+ system implementation.

Core implementation built from the UML class diagram. Data objects use
dataclasses; classes with behavior implement the methods declared in the UML.

Mapping to the assignment vocabulary:
  - "Task"      -> CareNeed (a recurring activity a pet requires) and its
                   scheduled instances, Event.
  - "Pet"       -> Pet (details + list of care needs).
  - "Owner"     -> Owner (multiple pets + access to all their needs).
  - "Scheduler" -> Scheduler (the "brain" that organizes needs into events).
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum


class AnimalType(Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    OTHER = "other"


class CareType(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDICATION = "medication"
    PLAY = "play"


class Recurrence(Enum):
    """How often a CareNeed repeats across days.

    DAILY  -> applies every day.
    WEEKLY -> applies only on the weekdays listed in ``days_of_week``.
    """

    DAILY = "daily"
    WEEKLY = "weekly"


class EventStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"


@dataclass
class PetAttributes:
    medications: list[str] = field(default_factory=list)
    food_requirements: str = ""
    exercise_requirements: str = ""
    notes: str = ""


@dataclass
class CareNeed:
    """A recurring activity a pet requires (the assignment's 'Task').

    Describes *what* care is needed and *how often*; the Scheduler turns these
    into concrete, time-bound Events on a Calendar.
    """

    id: int
    type: CareType
    frequency_per_day: int
    duration_minutes: int
    priority: int = 1  # higher number == higher priority
    completed: bool = False
    # How this need repeats across days. Defaults to DAILY so existing needs
    # (and the demo) keep their every-day behavior. When WEEKLY, the need only
    # applies on the weekdays in ``days_of_week`` (0 = Monday .. 6 = Sunday).
    recurrence: Recurrence = Recurrence.DAILY
    days_of_week: set[int] = field(default_factory=set)
    # Optional time of day the owner would like this to happen (e.g. a morning
    # walk). None means "no preference" -> the scheduler picks automatically.
    preferred_time: time | None = None

    def __post_init__(self) -> None:
        """Validate frequency, duration, and weekly recurrence settings."""
        if self.frequency_per_day < 1:
            raise ValueError("frequency_per_day must be at least 1")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.recurrence is Recurrence.WEEKLY:
            if not self.days_of_week:
                raise ValueError(
                    "weekly care needs must list at least one weekday in "
                    "days_of_week (0 = Monday .. 6 = Sunday)"
                )
            if any(d not in range(7) for d in self.days_of_week):
                raise ValueError("days_of_week values must be in 0..6")

    def occurs_on(self, day: date) -> bool:
        """Return True if this need should be scheduled on ``day``.

        Daily needs occur every day; weekly needs occur only on their listed
        weekdays. ``frequency_per_day`` then controls how many times it repeats
        on a day it does occur.
        """
        if self.recurrence is Recurrence.DAILY:
            return True
        return day.weekday() in self.days_of_week

    def mark_complete(self) -> None:
        """Mark this care need as done for the day."""
        self.completed = True


@dataclass
class Pet:
    """Stores pet details and the list of care needs it requires."""

    id: int
    name: str
    animal: AnimalType
    breed: str
    attributes: PetAttributes
    care_needs: list[CareNeed] = field(default_factory=list)

    def add_care_need(self, need: CareNeed) -> None:
        """Add a care need, replacing any existing need with the same id."""
        self.remove_care_need(need.id)
        self.care_needs.append(need)

    def remove_care_need(self, need_id: int) -> None:
        """Remove the care need with the given id, if present."""
        self.care_needs = [n for n in self.care_needs if n.id != need_id]

    def list_care_needs(self) -> list[CareNeed]:
        """Return care needs ordered by descending priority."""
        return sorted(self.care_needs, key=lambda n: n.priority, reverse=True)


@dataclass
class TimeSlot:
    start: datetime
    end: datetime

    @property
    def duration_minutes(self) -> float:
        """Return the length of this slot in minutes."""
        return (self.end - self.start).total_seconds() / 60

    def can_fit(self, minutes: int) -> bool:
        """Return True if an activity of the given length fits in this slot."""
        return self.duration_minutes >= minutes


@dataclass
class BlockedTime:
    id: int
    start: datetime
    end: datetime
    reason: str


@dataclass
class Event:
    """A concrete, scheduled instance of a care need on the calendar."""

    id: int
    type: CareType
    start: datetime
    end: datetime
    status: EventStatus
    pet_id: int
    care_need_id: int


@dataclass
class Conflict:
    """Two events whose times overlap.

    A conflict for a single owner means they'd need to be two places at once
    (e.g. walking two pets in the same minutes). ``overlap_minutes`` is how much
    the two events actually collide.
    """

    first: Event
    second: Event
    overlap_minutes: float

    @property
    def same_pet(self) -> bool:
        """True if both events belong to the same pet."""
        return self.first.pet_id == self.second.pet_id


@dataclass
class Notification:
    id: int
    message: str
    scheduled_for: datetime
    sent: bool = False

    def send(self) -> None:
        """Mark the notification as sent (stand-in for real delivery)."""
        self.sent = True


class Calendar:
    """Holds scheduled events and blocked-off time for an owner, and can
    compute the free slots left in a day."""

    # The window of a day the scheduler is allowed to place events in.
    DAY_START = time(7, 0)
    DAY_END = time(21, 0)

    def __init__(self, id: int) -> None:
        """Create an empty calendar with no events or blocked times."""
        self.id = id
        self.events: list[Event] = []
        self.blocked_times: list[BlockedTime] = []

    def add_event(self, event: Event) -> None:
        """Add a scheduled event to the calendar."""
        self.events.append(event)

    def remove_event(self, event_id: int) -> None:
        """Remove the event with the given id, if present."""
        self.events = [e for e in self.events if e.id != event_id]

    def add_blocked_time(self, block: BlockedTime) -> None:
        """Reserve a span of time so no events can be scheduled in it."""
        self.blocked_times.append(block)

    def get_available_slots(self, day: date) -> list[TimeSlot]:
        """Return the free TimeSlots on ``day`` between DAY_START and DAY_END,
        with all scheduled events and blocked times carved out."""
        day_start = datetime.combine(day, self.DAY_START)
        day_end = datetime.combine(day, self.DAY_END)

        # Collect everything that occupies time on this day.
        busy: list[TimeSlot] = []
        for event in self.events:
            if event.start.date() == day and event.status != EventStatus.MISSED:
                busy.append(TimeSlot(event.start, event.end))
        for block in self.blocked_times:
            if block.start.date() == day:
                busy.append(TimeSlot(block.start, block.end))

        # Clip to the day window and sort by start.
        busy = [
            TimeSlot(max(b.start, day_start), min(b.end, day_end))
            for b in busy
            if b.end > day_start and b.start < day_end
        ]
        busy.sort(key=lambda s: s.start)

        # Walk the timeline, emitting gaps between busy blocks.
        free: list[TimeSlot] = []
        cursor = day_start
        for block in busy:
            if block.start > cursor:
                free.append(TimeSlot(cursor, block.start))
            cursor = max(cursor, block.end)
        if cursor < day_end:
            free.append(TimeSlot(cursor, day_end))
        return free


class Owner:
    """Manages multiple pets and provides access to all of their care needs."""

    def __init__(self, id: int, name: str, email: str) -> None:
        """Create an owner with no pets and an empty calendar."""
        self.id = id
        self.name = name
        self.email = email
        self.pets: list[Pet] = []
        self.calendar = Calendar(id)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, replacing any existing pet with the same id."""
        self.remove_pet(pet.id)
        self.pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove the pet with the given id, if present."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def list_pets(self) -> list[Pet]:
        """Return a copy of the owner's list of pets."""
        return list(self.pets)

    def all_care_needs(self) -> list[tuple[Pet, CareNeed]]:
        """Return every care need across all pets, paired with its pet."""
        return [(pet, need) for pet in self.pets for need in pet.care_needs]

    def filter_care_needs(
        self,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
        care_type: CareType | None = None,
        min_priority: int | None = None,
    ) -> list[tuple[Pet, CareNeed]]:
        """Return (pet, need) pairs matching every supplied filter.

        All filters are optional and combine with AND; passing none returns
        everything (same as :meth:`all_care_needs`).

        Args:
            completed: Keep only needs whose ``completed`` flag matches this.
            pet_name: Keep only needs whose pet's name matches (case-insensitive).
            care_type: Keep only needs of this :class:`CareType`.
            min_priority: Keep only needs with priority >= this value.
        """
        target_name = pet_name.lower() if pet_name is not None else None

        results: list[tuple[Pet, CareNeed]] = []
        for pet, need in self.all_care_needs():
            if completed is not None and need.completed != completed:
                continue
            if target_name is not None and pet.name.lower() != target_name:
                continue
            if care_type is not None and need.type != care_type:
                continue
            if min_priority is not None and need.priority < min_priority:
                continue
            results.append((pet, need))
        return results


class Scheduler:
    """The "brain": retrieves care needs across pets, organizes them by
    priority, and places them into free calendar slots as Events."""

    def __init__(self, slot_gap_minutes: int = 0) -> None:
        """Create a scheduler that leaves ``slot_gap_minutes`` between events."""
        # Minimum gap to leave after each placed event.
        self.slot_gap_minutes = slot_gap_minutes
        self._next_event_id = 1

    def generate_schedule(
        self, pets: list[Pet], calendar: Calendar, day: date | None = None
    ) -> list[Event]:
        """Build a day's schedule of Events for the given pets.

        Care needs are expanded by ``frequency_per_day`` and placed
        highest-priority-first into the calendar's available slots. Events that
        can be placed are added to the calendar and returned.
        """
        day = day or date.today()

        # Expand each need into one placement request per required occurrence,
        # then order by priority (desc) so important care is scheduled first.
        requests: list[tuple[Pet, CareNeed]] = []
        for pet in pets:
            for need in pet.care_needs:
                if not need.occurs_on(day):
                    continue  # Weekly need that doesn't fall on this weekday.
                requests.extend((pet, need) for _ in range(need.frequency_per_day))
        requests.sort(key=lambda pn: pn[1].priority, reverse=True)

        scheduled: list[Event] = []
        for pet, need in requests:
            slot = self.find_slot(need, calendar, day)
            if slot is None:
                continue  # No room left today for this occurrence.
            end = slot.start + timedelta(minutes=need.duration_minutes)
            event = Event(
                id=self._next_event_id,
                type=need.type,
                start=slot.start,
                end=end,
                status=EventStatus.SCHEDULED,
                pet_id=pet.id,
                care_need_id=need.id,
            )
            self._next_event_id += 1
            calendar.add_event(event)  # Occupies the slot for later placements.
            scheduled.append(event)
        return scheduled

    def find_slot(
        self, need: CareNeed, calendar: Calendar, day: date | None = None
    ) -> TimeSlot | None:
        """Find a slot on ``day`` that fits ``need``.

        If the need has a ``preferred_time`` and it's still free, honor it.
        Otherwise (or if the preferred time is taken) fall back to the earliest
        available slot that fits. Returns a TimeSlot sized to the need's
        duration, or None if nothing fits, so callers can skip gracefully.
        """
        day = day or date.today()
        required = need.duration_minutes + self.slot_gap_minutes
        free_slots = calendar.get_available_slots(day)

        # Preferred time first: place it there if it lands inside a free slot
        # with enough room. If not, we just fall through to earliest-fit.
        if need.preferred_time is not None:
            wanted = datetime.combine(day, need.preferred_time)
            for free in free_slots:
                fits = wanted + timedelta(minutes=required)
                if free.start <= wanted and fits <= free.end:
                    return TimeSlot(
                        wanted, wanted + timedelta(minutes=need.duration_minutes)
                    )

        for free in free_slots:
            if free.can_fit(required):
                return TimeSlot(
                    free.start,
                    free.start + timedelta(minutes=need.duration_minutes),
                )
        return None

    def detect_conflicts(self, events: list[Event]) -> list[Conflict]:
        """Return every pair of overlapping events among ``events``.

        Two events conflict when their time ranges overlap at all, meaning a
        single owner can't do both — e.g. two pets scheduled for the same
        minutes. MISSED events are ignored since they no longer occupy time.

        Uses a sort-by-start sweep: events are ordered by start time, then each
        is compared only against still-"open" earlier events, so overlapping
        clusters are found without checking every pair.
        """
        active = [e for e in events if e.status != EventStatus.MISSED]
        active.sort(key=lambda e: e.start)

        conflicts: list[Conflict] = []
        for i, event in enumerate(active):
            for earlier in active[:i]:
                # Sorted by start, so `event.start >= earlier.start`. They
                # overlap iff this event starts before the earlier one ends.
                if event.start >= earlier.end:
                    continue
                overlap_end = min(event.end, earlier.end)
                overlap = (overlap_end - event.start).total_seconds() / 60
                if overlap > 0:
                    conflicts.append(Conflict(earlier, event, overlap))
        return conflicts


class TaskLog:
    """Records completed care events and answers history queries per pet."""

    def __init__(self) -> None:
        """Create an empty task log."""
        self.history: list[Event] = []

    def log_completed(self, event: Event, completed_at: datetime) -> None:
        """Mark an event completed at the given time and record it in history."""
        event.status = EventStatus.COMPLETED
        event.end = completed_at
        self.history.append(event)

    def get_history(self, pet_id: int) -> list[Event]:
        """Return the completed-event history for the given pet."""
        return [e for e in self.history if e.pet_id == pet_id]
