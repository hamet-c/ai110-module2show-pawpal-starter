"""PawPal+ system skeleton.

Class stubs generated from the UML class diagram. Data objects use
dataclasses; classes with behavior use plain classes with empty method stubs.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
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
    id: int
    type: CareType
    frequency_per_day: int
    duration_minutes: int
    priority: int


@dataclass
class Pet:
    id: int
    name: str
    animal: AnimalType
    breed: str
    attributes: PetAttributes
    care_needs: list[CareNeed] = field(default_factory=list)

    def add_care_need(self, need: CareNeed) -> None:
        ...

    def remove_care_need(self, need_id: int) -> None:
        ...

    def list_care_needs(self) -> list[CareNeed]:
        ...


@dataclass
class TimeSlot:
    start: datetime
    end: datetime


@dataclass
class BlockedTime:
    id: int
    start: datetime
    end: datetime
    reason: str


@dataclass
class Event:
    id: int
    type: CareType
    start: datetime
    end: datetime
    status: EventStatus
    pet_id: int


@dataclass
class Notification:
    id: int
    message: str
    scheduled_for: datetime
    sent: bool = False

    def send(self) -> None:
        ...


class Owner:
    def __init__(self, id: int, name: str, email: str) -> None:
        self.id = id
        self.name = name
        self.email = email
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        ...

    def remove_pet(self, pet_id: int) -> None:
        ...

    def list_pets(self) -> list[Pet]:
        ...


class Calendar:
    def __init__(self, id: int) -> None:
        self.id = id
        self.events: list[Event] = []
        self.blocked_times: list[BlockedTime] = []

    def add_event(self, event: Event) -> None:
        ...

    def remove_event(self, event_id: int) -> None:
        ...

    def add_blocked_time(self, block: BlockedTime) -> None:
        ...

    def get_available_slots(self, day: date) -> list[TimeSlot]:
        ...


class Scheduler:
    def generate_schedule(self, pets: list[Pet], calendar: Calendar) -> list[Event]:
        ...

    def find_slot(self, need: CareNeed, calendar: Calendar) -> TimeSlot:
        ...


class TaskLog:
    def __init__(self) -> None:
        self.history: list[Event] = []

    def log_completed(self, event: Event, completed_at: datetime) -> None:
        ...

    def get_history(self, pet_id: int) -> list[Event]:
        ...
