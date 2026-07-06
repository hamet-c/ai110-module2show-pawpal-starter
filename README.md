# PawPal+ (Module 2 Project)

**PawPal+** is a pet-care planning assistant. It turns a set of recurring care needs (walks, feeding, medication, play) across one or more pets into a conflict-free daily schedule, honoring priorities, preferred times, and the owner's busy hours. It ships with a Streamlit UI (`app.py`), a command-line demo (`main.py`), and a tested backend (`pawpal_system.py`).

## ✨ Features

The scheduling logic lives in `pawpal_system.py`. The algorithms it implements:

- **Priority-first placement** — `Scheduler.generate_schedule` expands every care need by its `frequency_per_day`, sorts all occurrences by priority (highest first), and places them in that order. Critical care (meds, feeding) gets the best times; low-priority tasks fill the gaps.
- **Sorting by time** — generated events are returned and displayed in chronological order (by start time), so the schedule reads top-to-bottom like a real day planner.
- **Free-slot search with no double-booking** — `Calendar.get_available_slots` computes the open gaps in a day by carving out existing events and blocked time; each placed event is committed to the calendar immediately, so the next task only sees genuinely free time.
- **Preferred times with automatic fallback** — a need may carry an optional `preferred_time`. `Scheduler.find_slot` honors it when that window is open, and otherwise silently falls back to the earliest slot that fits.
- **Daily & weekly recurrence** — `CareNeed.occurs_on(day)` decides whether a task applies to a date: `DAILY` needs occur every day; `WEEKLY` needs occur only on the weekdays in `days_of_week` (0 = Monday … 6 = Sunday).
- **Conflict warnings** — `Scheduler.detect_conflicts` runs a sort-by-start sweep over any list of events and reports every overlapping pair, including the overlap in minutes and whether it's the same pet or "two pets at once."
- **Blocked / busy time** — `Calendar.add_blocked_time` reserves spans (work, appointments) that the scheduler treats as unavailable.
- **Multi-criteria filtering** — `Owner.filter_care_needs` returns needs matching any combination of completion status, pet name, care type, and minimum priority (AND-combined).
- **Completion logging** — `TaskLog.log_completed` marks an event done and records it, and `get_history(pet_id)` returns a pet's completed-task history.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` builds a sample owner (Alex Rivera) with two pets and prints the day's schedule, the filtering demos, and a forced conflict:

```text
============================================
  Today's Schedule for Alex Rivera
  Sunday, July 05, 2026
============================================
  07:00-07:10  Milo   Medication
  07:10-07:25  Rex    Feed
  07:25-07:40  Rex    Feed
  07:40-07:50  Milo   Feed
  07:50-08:00  Milo   Feed
  08:00-08:30  Rex    Walk
  08:30-09:00  Rex    Walk
  09:00-09:25  Rex    Play
  09:25-09:45  Milo   Play
--------------------------------------------
  9 task(s) scheduled.
```

The remaining sections of the run demonstrate filtering and conflict detection:

```text
============================================
  Filtering Demos
============================================

  All care needs (6):
    Rex    feed        p4 todo
    Rex    walk        p3 todo
    Rex    play        p2 todo
    Milo   medication  p5 todo
    Milo   play        p1 todo
    Milo   feed        p4 done

  High priority (>= 4) (3):
    Rex    feed        p4 todo
    Milo   medication  p5 todo
    Milo   feed        p4 done

============================================
  Conflict Detection
============================================
  08:00-08:30  Rex    Walk
  08:15-08:45  Milo   Play

  ⚠  1 scheduling conflict(s) detected:
    Rex (walk) overlaps Milo (play) by 15 min — two pets at once
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
python -m pytest
================================================================================= test session starts =================================================================================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\miken\OneDrive\Desktop\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 5 items                                                                                                                                                                      

test\test_pawpal.py .....                                                                                                                                                        [100%]

================================================================================== 5 passed in 0.02s ==================================================================================
```
test_task_completion — mark_complete() flips a need's completed from False to True.
test_task_addition — adding a CareNeed to a pet raises its task count to 1.
test_sorting_chronological_order — 4 daily occurrences come back sorted by start time with no overlaps.
test_recurrence_daily_occurs_every_day — a completed daily need still occurs_on tomorrow and re-schedules.
test_conflict_detection_flags_duplicate_times — same-time events flag one conflict (30-min overlap); back-to-back events flag none.

## 📐 Smarter Scheduling


**Priority-first placement.** `Scheduler.generate_schedule` sorts every task by priority (highest first) before placing any of them, so the important stuff (meds, feeding) always gets the best times. Lower-priority tasks fill in whatever is left, and if the day runs out of room they're skipped rather than forcing an overlap.

**Preferred times, with an automatic fallback.** A task can carry an optional `preferred_time`. If that time is still open, `find_slot` places it there; if it's taken or outside the day window, the task quietly falls back to the earliest slot that fits. Tasks with no preferred time are placed automatically, so setting a time is optional.

**No double-booking.** Each task the scheduler places is added to the calendar right away, so the next task only sees the time that's actually free. That means the scheduler never books two things at once for a single owner. `Calendar.get_available_slots` is what carves out the busy time (existing events plus any blocked-off spans).

**Conflict detection as a backstop.** The calendar itself doesn't stop you from adding overlapping events (from a previous run, a manual entry, an import, etc.), so `Scheduler.detect_conflicts` scans a list of events and reports any that overlap, including how many minutes they collide and whether it's the same pet. This is the warning that catches clashes the scheduler didn't create.

**Recurring tasks.** A `CareNeed` repeats either `DAILY` (every day) or `WEEKLY` on specific weekdays via `days_of_week`. `CareNeed.occurs_on(day)` decides whether a task applies to a given date, so a "walk only on Sat/Sun" task won't show up on a Tuesday. `frequency_per_day` then controls how many times it repeats on a day it does occur.

**Filtering.** `Owner.filter_care_needs` returns tasks matching any combination of filters (completion status, pet name, care type, minimum priority), which makes it easy to answer questions like "what does Milo still have left to do today?"

## 📖 Demo Walkthrough

Run the app with `streamlit run app.py`. It has three tabs and a sidebar.

**What you can do:**
- **Sidebar** — set the owner name and add pets.
- **📋 Tasks** — add care needs (type, duration, times per day, priority, daily/weekly), and filter them.
- **🗓️ Schedule** — pick a day, block off busy time, and generate the plan.
- **✅ Review & History** — mark tasks complete and view history.

**Example workflow:**
1. Add a pet in the sidebar.
2. In **Tasks**, add a couple of care needs.
3. In **Schedule**, click **Generate schedule** to see today's plan.
4. In **Review**, mark a task complete.

**What the scheduler shows:** tasks are placed highest-priority-first but listed in time order, never double-booked, and any overlapping events are flagged as conflicts.
