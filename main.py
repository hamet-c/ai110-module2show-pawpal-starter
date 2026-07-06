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

from datetime import date

from pawpal_system import (
    AnimalType,
    CareNeed,
    CareType,
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

    owner.add_pet(rex)
    owner.add_pet(milo)
    return owner


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


def main() -> None:
    owner = build_owner()
    print_todays_schedule(owner, day=date.today())


if __name__ == "__main__":
    main()
