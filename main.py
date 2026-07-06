"""PawPal+ demo.

Wires the core classes together into a small end-to-end run:
  1. Create an Owner.
  2. Give the Owner two Pets.
  3. Add care needs (the assignment's "Tasks") of different durations,
     frequencies, and priorities.
  4. Let the Scheduler organize them into timed Events.
  5. Print "Today's Schedule" to the terminal.

Run with:  python main.py
"""

from datetime import date, datetime

from pawpal_system import (
    AnimalType,
    CareNeed,
    CareType,
    Event,
    EventStatus,
    Owner,
    Pet,
    PetAttributes,
    Scheduler,
)


def build_owner() -> Owner:
    """Create an owner with two pets and several care needs."""
    owner = Owner(id=1, name="Alex Rivera", email="alex@example.com")

    # --- Pet 1: a dog with walks and meals. ---
    rex = Pet(
        id=1,
        name="Rex",
        animal=AnimalType.DOG,
        breed="Labrador",
        attributes=PetAttributes(
            food_requirements="1 cup kibble per meal",
            exercise_requirements="Two 30-minute walks daily",
        ),
    )
    rex.add_care_need(
        CareNeed(id=1, type=CareType.FEED, frequency_per_day=2,
                 duration_minutes=15, priority=4)
    )
    rex.add_care_need(
        CareNeed(id=2, type=CareType.WALK, frequency_per_day=2,
                 duration_minutes=30, priority=3)
    )

    # --- Pet 2: a cat that needs daily medication. ---
    milo = Pet(
        id=2,
        name="Milo",
        animal=AnimalType.CAT,
        breed="Tabby",
        attributes=PetAttributes(
            medications=["insulin"],
            food_requirements="Wet food, twice daily",
        ),
    )
    milo.add_care_need(
        CareNeed(id=3, type=CareType.MEDICATION, frequency_per_day=1,
                 duration_minutes=10, priority=5)
    )
    milo.add_care_need(
        CareNeed(id=4, type=CareType.PLAY, frequency_per_day=1,
                 duration_minutes=20, priority=1)
    )

    # A few extra needs added out of priority/type order on purpose, so the
    # filtering demo has something interesting to sort and select from. One is
    # pre-marked complete to exercise the ``completed`` filter.
    rex.add_care_need(
        CareNeed(id=5, type=CareType.PLAY, frequency_per_day=1,
                 duration_minutes=25, priority=2)
    )
    milo_meds_done = CareNeed(id=6, type=CareType.FEED, frequency_per_day=2,
                              duration_minutes=10, priority=4)
    milo_meds_done.mark_complete()
    milo.add_care_need(milo_meds_done)

    owner.add_pet(rex)
    owner.add_pet(milo)
    return owner


def print_filter_demos(owner: Owner) -> None:
    """Show a few uses of Owner.filter_care_needs in the terminal."""

    def show(label: str, pairs: list[tuple[Pet, CareNeed]]) -> None:
        print(f"\n  {label} ({len(pairs)}):")
        if not pairs:
            print("    (none)")
            return
        for pet, need in pairs:
            done = "done" if need.completed else "todo"
            print(f"    {pet.name:<6} {need.type.value:<11} "
                  f"p{need.priority} {done}")

    print("\n" + "=" * 44)
    print("  Filtering Demos")
    print("=" * 44)

    show("All care needs", owner.filter_care_needs())
    show("Only Rex's needs", owner.filter_care_needs(pet_name="Rex"))
    show("Medication needs", owner.filter_care_needs(care_type=CareType.MEDICATION))
    show("High priority (>= 4)", owner.filter_care_needs(min_priority=4))
    show("Still to do", owner.filter_care_needs(completed=False))
    show("Milo, not yet done", owner.filter_care_needs(pet_name="Milo", completed=False))


def print_todays_schedule(owner: Owner, day: date) -> None:
    """Generate and print the day's schedule for all of an owner's pets."""
    scheduler = Scheduler(slot_gap_minutes=10)
    events = scheduler.generate_schedule(owner.list_pets(), owner.calendar, day)

    # Index pets by id so we can show names next to each event.
    pets_by_id = {pet.id: pet for pet in owner.list_pets()}

    print("=" * 44)
    print(f"  Today's Schedule for {owner.name}")
    print(f"  {day:%A, %B %d, %Y}")
    print("=" * 44)

    if not events:
        print("  No care tasks scheduled today.")
        return

    # Show events in chronological order.
    for event in sorted(events, key=lambda e: e.start):
        pet_name = pets_by_id[event.pet_id].name
        window = f"{event.start:%H:%M}-{event.end:%H:%M}"
        activity = event.type.value.capitalize()
        print(f"  {window}  {pet_name:<6} {activity}")

    print("-" * 44)
    print(f"  {len(events)} task(s) scheduled.")


def print_conflict_demo(owner: Owner, day: date) -> None:
    """Force two pets into the same time slot, then detect and warn.

    The scheduler auto-spaces events it places itself, so a real clash won't
    happen through generate_schedule alone. To demonstrate the warning, we drop
    two events for two different pets onto the calendar at overlapping times
    (as could happen with hand-entered or imported events) and let
    detect_conflicts find them.
    """
    scheduler = Scheduler()
    pets_by_id = {pet.id: pet for pet in owner.list_pets()}

    # Rex walks 08:00-08:30; Milo's playtime is booked 08:15-08:45 -> they
    # collide for 15 minutes, and one owner can't do both at once.
    rex_walk = Event(
        id=901, type=CareType.WALK,
        start=datetime.combine(day, datetime.min.time()).replace(hour=8, minute=0),
        end=datetime.combine(day, datetime.min.time()).replace(hour=8, minute=30),
        status=EventStatus.SCHEDULED, pet_id=1, care_need_id=2,
    )
    milo_play = Event(
        id=902, type=CareType.PLAY,
        start=datetime.combine(day, datetime.min.time()).replace(hour=8, minute=15),
        end=datetime.combine(day, datetime.min.time()).replace(hour=8, minute=45),
        status=EventStatus.SCHEDULED, pet_id=2, care_need_id=4,
    )
    events = [rex_walk, milo_play]

    print("\n" + "=" * 44)
    print("  Conflict Detection")
    print("=" * 44)
    for event in sorted(events, key=lambda e: e.start):
        pet_name = pets_by_id.get(event.pet_id)
        pet_name = pet_name.name if pet_name else f"pet {event.pet_id}"
        print(f"  {event.start:%H:%M}-{event.end:%H:%M}  {pet_name:<6} "
              f"{event.type.value.capitalize()}")

    conflicts = scheduler.detect_conflicts(events)
    if not conflicts:
        print("\n  No conflicts. ✓")
        return

    print(f"\n  ⚠  {len(conflicts)} scheduling conflict(s) detected:")
    for c in conflicts:
        first = pets_by_id.get(c.first.pet_id)
        second = pets_by_id.get(c.second.pet_id)
        first = first.name if first else f"pet {c.first.pet_id}"
        second = second.name if second else f"pet {c.second.pet_id}"
        scope = "same pet" if c.same_pet else "two pets at once"
        print(f"    {first} ({c.first.type.value}) overlaps "
              f"{second} ({c.second.type.value}) by "
              f"{c.overlap_minutes:.0f} min — {scope}")


def main() -> None:
    owner = build_owner()
    print_todays_schedule(owner, day=date.today())
    print_filter_demos(owner)
    print_conflict_demo(owner, day=date.today())


if __name__ == "__main__":
    main()
