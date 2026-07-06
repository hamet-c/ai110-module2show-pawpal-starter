"""PawPal+ — interactive Streamlit demo.

A thin UI layer over ``pawpal_system``. Every section here drives real backend
methods: pets and care needs, daily/weekly recurrence, blocked time, filtering,
schedule generation, conflict detection, and completion logging.
"""

from datetime import date, datetime, time

import streamlit as st

from pawpal_system import (
    AnimalType,
    BlockedTime,
    CareNeed,
    CareType,
    EventStatus,
    Owner,
    Pet,
    PetAttributes,
    Recurrence,
    Scheduler,
    TaskLog,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# --- Mappings from friendly UI values to the backend's typed values ---

# Species dropdown -> AnimalType enum.
ANIMAL_TYPES = {
    "dog": AnimalType.DOG,
    "cat": AnimalType.CAT,
    "bird": AnimalType.BIRD,
    "other": AnimalType.OTHER,
}

# Care-type dropdown -> CareType enum. Chosen explicitly instead of guessed.
CARE_TYPES = {
    "walk": CareType.WALK,
    "feed": CareType.FEED,
    "medication": CareType.MEDICATION,
    "play": CareType.PLAY,
}

# Priority dropdown -> CareNeed.priority (int; higher == more important).
PRIORITY_LEVELS = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABELS = {v: k for k, v in PRIORITY_LEVELS.items()}

# Weekday index (0 = Monday .. 6 = Sunday) -> label, matching CareNeed.days_of_week.
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# --------------------------------------------------------------------------- #
# Session state: one Owner + TaskLog kept alive across Streamlit reruns.
# --------------------------------------------------------------------------- #
if "owner" not in st.session_state:
    st.session_state.owner = Owner(id=1, name="Jordan", email="owner@example.com")
    st.session_state.task_log = TaskLog()
    st.session_state.next_pet_id = 1
    st.session_state.next_need_id = 1
    st.session_state.next_block_id = 1
    st.session_state.last_events = []

owner: Owner = st.session_state.owner
task_log: TaskLog = st.session_state.task_log


def pet_label(pet: Pet) -> str:
    """Human-readable label for a pet selector."""
    return f"{pet.name} ({pet.animal.value})"


# --------------------------------------------------------------------------- #
# Sidebar: owner + pet management.
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("🐾 PawPal+")
    st.caption("Pet care planning assistant")

    st.subheader("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)

    st.divider()
    st.subheader("Add a pet")
    with st.form("add_pet", clear_on_submit=True):
        new_pet_name = st.text_input("Pet name", value="Mochi")
        new_species = st.selectbox("Species", list(ANIMAL_TYPES))
        new_breed = st.text_input("Breed", value="Mixed")
        if st.form_submit_button("Add pet", use_container_width=True):
            if not new_pet_name.strip():
                st.error("Give the pet a name.")
            else:
                owner.add_pet(
                    Pet(
                        id=st.session_state.next_pet_id,
                        name=new_pet_name.strip(),
                        animal=ANIMAL_TYPES[new_species],
                        breed=new_breed,
                        attributes=PetAttributes(),
                    )
                )
                st.session_state.next_pet_id += 1
                st.success(f"Added {new_pet_name}.")

    pets = owner.list_pets()
    if pets:
        st.caption(f"{len(pets)} pet(s): " + ", ".join(p.name for p in pets))


st.title("🐾 PawPal+ Care Planner")

pets = owner.list_pets()
if not pets:
    st.info("👈 Add a pet in the sidebar to get started.")
    st.stop()

# Which pet are we editing tasks for? Select by id, not by Pet object:
# Streamlit deep-copies widget values, so a Pet chosen directly from the
# selectbox would be a copy — tasks added to it would never reach the owner.
pets_by_id = {p.id: p for p in pets}
selected_id = st.selectbox(
    "Active pet",
    list(pets_by_id),
    format_func=lambda pid: pet_label(pets_by_id[pid]),
    key="active_pet",
)
pet = pets_by_id[selected_id]

tab_tasks, tab_schedule, tab_review = st.tabs(
    ["📋 Tasks", "🗓️ Schedule", "✅ Review & History"]
)


# --------------------------------------------------------------------------- #
# Tab 1 — Tasks: add care needs (daily or weekly) and filter them.
# --------------------------------------------------------------------------- #
with tab_tasks:
    st.subheader(f"Care needs for {pet.name}")

    with st.form("add_task", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            care_type = st.selectbox("Type", list(CARE_TYPES))
        with c2:
            duration = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )
        with c3:
            frequency = st.number_input(
                "Times per day", min_value=1, max_value=12, value=1
            )
        with c4:
            priority = st.selectbox("Priority", list(PRIORITY_LEVELS), index=2)

        recurrence_choice = st.radio(
            "Recurrence", ["Daily", "Weekly"], horizontal=True
        )
        selected_days = st.multiselect(
            "On which days? (weekly only)",
            options=list(range(7)),
            format_func=lambda i: WEEKDAYS[i],
            default=[0, 2, 4],
        )

        pick_time = st.checkbox("Pin a preferred start time")
        preferred_time = (
            st.time_input("Preferred start", value=time(9, 0)) if pick_time else None
        )

        if st.form_submit_button("Add task", type="primary"):
            is_weekly = recurrence_choice == "Weekly"
            if is_weekly and not selected_days:
                st.error("Weekly tasks need at least one day selected.")
            else:
                try:
                    need = CareNeed(
                        id=st.session_state.next_need_id,
                        type=CARE_TYPES[care_type],
                        frequency_per_day=int(frequency),
                        duration_minutes=int(duration),
                        priority=PRIORITY_LEVELS[priority],
                        recurrence=(
                            Recurrence.WEEKLY if is_weekly else Recurrence.DAILY
                        ),
                        days_of_week=set(selected_days) if is_weekly else set(),
                        preferred_time=preferred_time,
                    )
                    pet.add_care_need(need)
                    st.session_state.next_need_id += 1
                    # Tasks changed -> the last schedule is now stale. Drop it so
                    # the Schedule tab prompts a fresh generate instead of showing
                    # an out-of-date (possibly empty) plan.
                    st.session_state.last_events = []
                    st.success(f"Added {care_type} for {pet.name}. Re-generate the schedule to include it.")
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()

    # ---- Filtering (Owner.filter_care_needs) across ALL pets ----------------
    st.markdown("#### Browse care needs")
    f1, f2, f3 = st.columns(3)
    with f1:
        f_type = st.selectbox("Filter type", ["(any)"] + list(CARE_TYPES))
    with f2:
        f_status = st.selectbox("Status", ["(any)", "pending", "completed"])
    with f3:
        f_min_priority = st.selectbox(
            "Min priority", ["(any)"] + list(PRIORITY_LEVELS)
        )

    completed_filter = (
        None if f_status == "(any)" else (f_status == "completed")
    )
    results = owner.filter_care_needs(
        completed=completed_filter,
        care_type=None if f_type == "(any)" else CARE_TYPES[f_type],
        min_priority=(
            None if f_min_priority == "(any)" else PRIORITY_LEVELS[f_min_priority]
        ),
    )

    if results:
        st.dataframe(
            [
                {
                    "pet": p.name,
                    "type": n.type.value,
                    "minutes": n.duration_minutes,
                    "per day": n.frequency_per_day,
                    "priority": PRIORITY_LABELS.get(n.priority, n.priority),
                    "recurrence": n.recurrence.value,
                    "days": (
                        ", ".join(WEEKDAYS[d] for d in sorted(n.days_of_week))
                        if n.days_of_week
                        else "—"
                    ),
                    "preferred": (
                        n.preferred_time.strftime("%H:%M")
                        if n.preferred_time
                        else "auto"
                    ),
                    "done": "✅" if n.completed else "⬜",
                }
                for p, n in results
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No care needs match these filters.")


# --------------------------------------------------------------------------- #
# Tab 2 — Schedule: blocked time, generate, and conflict detection.
# --------------------------------------------------------------------------- #
with tab_schedule:
    st.subheader("Build a day's schedule")

    plan_day = st.date_input("Schedule for", value=date.today())

    with st.expander("Block off busy time (optional)"):
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            block_start = st.time_input("Busy from", value=time(12, 0))
        with b2:
            block_end = st.time_input("Busy until", value=time(13, 0))
        with b3:
            block_reason = st.text_input("Reason", value="Lunch / work")
        if st.button("Add blocked time"):
            start_dt = datetime.combine(plan_day, block_start)
            end_dt = datetime.combine(plan_day, block_end)
            if end_dt <= start_dt:
                st.error("'Busy until' must be after 'busy from'.")
            else:
                owner.calendar.add_blocked_time(
                    BlockedTime(
                        id=st.session_state.next_block_id,
                        start=start_dt,
                        end=end_dt,
                        reason=block_reason,
                    )
                )
                st.session_state.next_block_id += 1
                st.success(f"Blocked {block_start:%H:%M}–{block_end:%H:%M}.")

    if owner.calendar.blocked_times:
        st.caption("Blocked times:")
        st.dataframe(
            [
                {
                    "from": b.start.strftime("%H:%M"),
                    "until": b.end.strftime("%H:%M"),
                    "reason": b.reason,
                }
                for b in owner.calendar.blocked_times
                if b.start.date() == plan_day
            ]
            or [{"from": "—", "until": "—", "reason": "none on this day"}],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # Warn up front if there's nothing to schedule, so pressing Generate with an
    # empty task list gives a clear reason instead of a blank result.
    total_needs = sum(len(p.care_needs) for p in owner.list_pets())
    needs_today = sum(
        1
        for p in owner.list_pets()
        for n in p.care_needs
        if n.occurs_on(plan_day)
    )
    if total_needs == 0:
        st.warning("No care needs added yet — add some in the 📋 Tasks tab first.")
    elif needs_today == 0:
        st.warning(
            f"You have {total_needs} task(s), but none recur on "
            f"{plan_day:%A}. Try a daily task or a different day."
        )

    if st.button("⚙️ Generate schedule", type="primary"):
        # Fresh events each run so re-clicking doesn't stack old placements;
        # keep any blocked times the user configured.
        owner.calendar.events.clear()
        scheduler = Scheduler(slot_gap_minutes=5)
        events = scheduler.generate_schedule(
            owner.list_pets(), owner.calendar, day=plan_day
        )
        st.session_state.last_events = events
        if not events:
            st.warning(
                f"Nothing was placed for {plan_day:%A, %b %d} — no task recurs "
                "on that day, or the day is fully blocked."
            )

    events = st.session_state.last_events
    if events:
        pet_names = {p.id: p.name for p in owner.list_pets()}
        ordered = sorted(events, key=lambda e: e.start)
        st.success(f"Placed {len(events)} event(s) on {plan_day:%A, %b %d}.")
        st.dataframe(
            [
                {
                    "start": e.start.strftime("%H:%M"),
                    "end": e.end.strftime("%H:%M"),
                    "pet": pet_names.get(e.pet_id, e.pet_id),
                    "type": e.type.value,
                    "status": e.status.value,
                }
                for e in ordered
            ],
            use_container_width=True,
            hide_index=True,
        )

        # ---- Conflict detection (Scheduler.detect_conflicts) ---------------
        scheduler = Scheduler()
        conflicts = scheduler.detect_conflicts(events)
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
            for c in conflicts:
                scope = "same pet" if c.same_pet else "two pets at once"
                st.write(
                    f"- **{c.first.type.value}** vs **{c.second.type.value}** "
                    f"overlap by {c.overlap_minutes:.0f} min ({scope})"
                )
        else:
            st.info("✅ No conflicts — every task has its own time.")
    else:
        st.caption("No schedule yet. Configure tasks, then generate.")


# --------------------------------------------------------------------------- #
# Tab 3 — Review & History: complete events (TaskLog) and view history.
# --------------------------------------------------------------------------- #
with tab_review:
    st.subheader("Mark tasks complete")

    events = st.session_state.last_events
    pending = [e for e in events if e.status == EventStatus.SCHEDULED]
    if pending:
        pet_names = {p.id: p.name for p in owner.list_pets()}
        for e in sorted(pending, key=lambda e: e.start):
            cols = st.columns([3, 1])
            cols[0].write(
                f"**{e.start:%H:%M}** — {pet_names.get(e.pet_id, e.pet_id)} · "
                f"{e.type.value}"
            )
            if cols[1].button("Complete", key=f"done_{e.id}"):
                task_log.log_completed(e, datetime.now())
                st.rerun()
    else:
        st.caption("No scheduled events waiting. Generate a schedule first.")

    st.divider()
    st.subheader("Completion history")
    all_history = [e for p in owner.list_pets() for e in task_log.get_history(p.id)]
    if all_history:
        pet_names = {p.id: p.name for p in owner.list_pets()}
        st.dataframe(
            [
                {
                    "pet": pet_names.get(e.pet_id, e.pet_id),
                    "type": e.type.value,
                    "completed at": e.end.strftime("%Y-%m-%d %H:%M"),
                }
                for e in all_history
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Nothing completed yet.")
