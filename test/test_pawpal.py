"""Simple tests for the PawPal+ system.

Runnable two ways:
    pytest test/test_pawpal.py
    python test/test_pawpal.py
"""

import os
import sys

# Allow running directly (python test/test_pawpal.py) by putting the project
# root on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import (
    AnimalType,
    CareNeed,
    CareType,
    Pet,
    PetAttributes,
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


if __name__ == "__main__":
    test_task_completion()
    test_task_addition()
    print("All tests passed.")
