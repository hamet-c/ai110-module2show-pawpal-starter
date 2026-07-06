# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

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

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:
============================================
  Today's Schedule for Alex Rivera
  Sunday, July 05, 2026
============================================
  07:00-07:10  Milo   Medication
  07:10-07:25  Rex    Feed
  07:25-07:40  Rex    Feed
  07:40-08:10  Rex    Walk
  08:10-08:40  Rex    Walk
  08:40-09:00  Milo   Play
--------------------------------------------
  6 task(s) scheduled.

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
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
```

## 📐 Smarter Scheduling


**Priority-first placement.** `Scheduler.generate_schedule` sorts every task by priority (highest first) before placing any of them, so the important stuff (meds, feeding) always gets the best times. Lower-priority tasks fill in whatever is left, and if the day runs out of room they're skipped rather than forcing an overlap.

**Preferred times, with an automatic fallback.** A task can carry an optional `preferred_time`. If that time is still open, `find_slot` places it there; if it's taken or outside the day window, the task quietly falls back to the earliest slot that fits. Tasks with no preferred time are placed automatically, so setting a time is optional.

**No double-booking.** Each task the scheduler places is added to the calendar right away, so the next task only sees the time that's actually free. That means the scheduler never books two things at once for a single owner. `Calendar.get_available_slots` is what carves out the busy time (existing events plus any blocked-off spans).

**Conflict detection as a backstop.** The calendar itself doesn't stop you from adding overlapping events (from a previous run, a manual entry, an import, etc.), so `Scheduler.detect_conflicts` scans a list of events and reports any that overlap, including how many minutes they collide and whether it's the same pet. This is the warning that catches clashes the scheduler didn't create.

**Recurring tasks.** A `CareNeed` repeats either `DAILY` (every day) or `WEEKLY` on specific weekdays via `days_of_week`. `CareNeed.occurs_on(day)` decides whether a task applies to a given date, so a "walk only on Sat/Sun" task won't show up on a Tuesday. `frequency_per_day` then controls how many times it repeats on a day it does occur.

**Filtering.** `Owner.filter_care_needs` returns tasks matching any combination of filters (completion status, pet name, care type, minimum priority), which makes it easy to answer questions like "what does Milo still have left to do today?"

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
