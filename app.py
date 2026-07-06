from datetime import time

import streamlit as st

from pawpal_system import (
    AnimalType,
    CareNeed,
    CareType,
    Owner,
    Pet,
    PetAttributes,
    Scheduler,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Mappings from friendly UI values to the backend's typed values ---

# Species dropdown -> AnimalType enum.
ANIMAL_TYPES = {
    "dog": AnimalType.DOG,
    "cat": AnimalType.CAT,
    "other": AnimalType.OTHER,
}

# Priority dropdown -> CareNeed.priority (int; higher == more important).
PRIORITY_LEVELS = {"low": 1, "medium": 2, "high": 3}

# Task title keywords -> CareType. CareNeed has no free-text title, only a
# typed category, so we guess the category from the title and keep the title
# separately for display.
CARE_TYPE_KEYWORDS = {
    "walk": CareType.WALK,
    "feed": CareType.FEED,
    "food": CareType.FEED,
    "med": CareType.MEDICATION,
    "pill": CareType.MEDICATION,
    "play": CareType.PLAY,
}


def guess_care_type(title: str) -> CareType:
    """Pick a CareType from a task title, defaulting to PLAY."""
    lowered = title.lower()
    for keyword, care_type in CARE_TYPE_KEYWORDS.items():
        if keyword in lowered:
            return care_type
    return CareType.PLAY

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", list(ANIMAL_TYPES))
breed = st.text_input("Breed", value="Mixed")

# Create the Owner once and keep it in the session "vault" so it survives
# reruns. We track the id counter for care needs alongside it.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(id=1, name=owner_name, email="owner@example.com")
    st.session_state.next_need_id = 1

owner = st.session_state.owner

# Register (or refresh) the pet from the current inputs. Pet id 1 is reused, so
# add_pet replaces it rather than piling up duplicates on every rerun.
if st.button("Add / update pet"):
    pet = Pet(
        id=1,
        name=pet_name,
        animal=ANIMAL_TYPES[species],
        breed=breed,
        attributes=PetAttributes(),
    )
    owner.add_pet(pet)
    st.success(f"Pet '{pet.name}' ({pet.animal.value}) is set up for {owner.name}.")

pet = next(iter(owner.list_pets()), None)

st.markdown("### Tasks")
st.caption("Add care needs for your pet. These feed directly into the scheduler.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    frequency = st.number_input("Times per day", min_value=1, max_value=12, value=1)
with col4:
    priority = st.selectbox("Priority", list(PRIORITY_LEVELS), index=2)

# Optional preferred time. Off by default -> the scheduler places it
# automatically; check the box to pin a start time you'd like.
pick_time = st.checkbox("Pick a preferred time (otherwise scheduled automatically)")
preferred_time = st.time_input("Preferred start time", value=time(9, 0)) if pick_time else None

if st.button("Add task"):
    if pet is None:
        st.error("Add a pet first, then add its tasks.")
    else:
        need = CareNeed(
            id=st.session_state.next_need_id,
            type=guess_care_type(task_title),
            frequency_per_day=int(frequency),
            duration_minutes=int(duration),
            priority=PRIORITY_LEVELS[priority],
            preferred_time=preferred_time,
        )
        pet.add_care_need(need)
        st.session_state.next_need_id += 1
        when = preferred_time.strftime("%H:%M") if preferred_time else "auto"
        st.success(
            f"Added '{task_title}' ({need.type.value}) to {pet.name} — time: {when}."
        )

if pet is not None and pet.care_needs:
    st.write(f"Current tasks for {pet.name} (highest priority first):")
    st.table(
        [
            {
                "type": n.type.value,
                "minutes": n.duration_minutes,
                "per day": n.frequency_per_day,
                "priority": n.priority,
            }
            for n in pet.list_care_needs()
        ]
    )
else:
    st.info("No tasks yet. Add a pet and then a task above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Places today's care needs into free calendar slots, highest priority first.")

if st.button("Generate schedule"):
    if pet is None or not pet.care_needs:
        st.error("Add a pet and at least one task before generating a schedule.")
    else:
        # A fresh calendar each run so re-clicking doesn't stack old events.
        owner.calendar.events.clear()
        scheduler = Scheduler()
        events = scheduler.generate_schedule(owner.list_pets(), owner.calendar)

        if not events:
            st.warning("No events could be placed — the day may be full.")
        else:
            st.success(f"Scheduled {len(events)} event(s).")
            st.table(
                [
                    {
                        "type": e.type.value,
                        "start": e.start.strftime("%H:%M"),
                        "end": e.end.strftime("%H:%M"),
                        "status": e.status.value,
                    }
                    for e in sorted(events, key=lambda e: e.start)
                ]
            )
