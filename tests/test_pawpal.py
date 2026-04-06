from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ── helpers ──────────────────────────────────────────────────────────────────

def make_owner(time_available: int = 300) -> Owner:
    return Owner(name="Alex", time_available=time_available)


def make_scheduler(pets: list[Pet], time_available: int = 300) -> Scheduler:
    owner = make_owner(time_available)
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner=owner)


# ── existing tests ────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    task = Task(name="Walk", category="walk", duration=30, priority=3)
    assert task.is_completed is False
    task.complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    assert len(pet.get_tasks()) == 0
    task = Task(name="Feed", category="feed", duration=10, priority=4)
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1


# ── edge case: pet with no tasks ──────────────────────────────────────────────

def test_pet_with_no_tasks_returns_empty_list():
    pet = Pet(name="Whiskers", species="cat", breed="Siamese", age=2)
    assert pet.get_tasks() == []


def test_scheduler_with_no_tasks_returns_empty_schedule():
    pet = Pet(name="Whiskers", species="cat", breed="Siamese", age=2)
    scheduler = make_scheduler([pet])
    scheduled, deferred, overlaps = scheduler.generate_plan()
    assert scheduled == []
    assert deferred == []
    assert overlaps == []


def test_scheduler_with_no_pets_returns_empty_schedule():
    scheduler = make_scheduler([])
    scheduled, deferred, overlaps = scheduler.generate_plan()
    assert scheduled == []
    assert deferred == []
    assert overlaps == []


# ── sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """Tasks are ordered earliest preferred_hour first."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t_noon = Task(name="Lunch walk", category="walk", duration=20, priority=3, preferred_hour=12)
    t_morning = Task(name="Morning feed", category="feed", duration=10, priority=3, preferred_hour=8)
    t_evening = Task(name="Evening meds", category="meds", duration=5, priority=5, preferred_hour=18)
    for t in [t_noon, t_morning, t_evening]:
        pet.add_task(t)

    scheduler = make_scheduler([pet])
    result = scheduler.sort_by_time([t_noon, t_morning, t_evening])

    assert result == [t_morning, t_noon, t_evening]


def test_sort_by_time_places_no_hour_tasks_at_end():
    """Tasks with preferred_hour=None sort after all timed tasks."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t_timed = Task(name="Walk", category="walk", duration=30, priority=3, preferred_hour=9)
    t_untimed = Task(name="Grooming", category="grooming", duration=45, priority=2)
    for t in [t_untimed, t_timed]:
        pet.add_task(t)

    scheduler = make_scheduler([pet])
    result = scheduler.sort_by_time([t_untimed, t_timed])

    assert result.index(t_timed) < result.index(t_untimed)


def test_sort_by_time_stable_with_equal_hours():
    """Two tasks at the same preferred_hour both appear in the result."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t1 = Task(name="Feed AM", category="feed", duration=10, priority=4, preferred_hour=8)
    t2 = Task(name="Meds AM", category="meds", duration=5, priority=5, preferred_hour=8)
    for t in [t1, t2]:
        pet.add_task(t)

    scheduler = make_scheduler([pet])
    result = scheduler.sort_by_time([t1, t2])

    assert len(result) == 2
    assert t1 in result
    assert t2 in result
    assert result[0].preferred_hour == 8
    assert result[1].preferred_hour == 8


# ── recurrence logic ──────────────────────────────────────────────────────────

def test_daily_task_complete_returns_next_day_task():
    """Completing a daily task produces a new task due the following day."""
    today = date.today()
    task = Task(
        name="Morning walk",
        category="walk",
        duration=30,
        priority=3,
        recurrence="daily",
        due_date=today,
    )
    next_task = task.complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.name == task.name
    assert next_task.is_completed is False


def test_weekly_task_complete_returns_next_week_task():
    """Completing a weekly task produces a new task due seven days later."""
    today = date.today()
    task = Task(
        name="Bath",
        category="grooming",
        duration=60,
        priority=2,
        recurrence="weekly",
        due_date=today,
    )
    next_task = task.complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_one_off_task_complete_returns_none():
    """Completing a non-recurring task returns None (no follow-up task)."""
    task = Task(name="Vet visit", category="meds", duration=90, priority=5)
    result = task.complete()
    assert result is None


def test_pet_complete_task_appends_next_occurrence():
    """pet.complete_task() automatically appends the next recurring task."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    task = Task(
        name="Walk",
        category="walk",
        duration=30,
        priority=3,
        recurrence="daily",
        due_date=date.today(),
    )
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1

    pet.complete_task(task)

    assert len(pet.get_tasks()) == 2
    next_task = pet.get_tasks()[1]
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.is_completed is False


def test_pet_complete_task_one_off_does_not_append():
    """Completing a one-off task does not grow the task list."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    task = Task(name="Vet", category="meds", duration=60, priority=5)
    pet.add_task(task)

    pet.complete_task(task)

    assert len(pet.get_tasks()) == 1


def test_daily_task_complete_without_due_date_uses_today():
    """A daily task with no explicit due_date defaults to today when computing next."""
    task = Task(name="Feed", category="feed", duration=10, priority=4, recurrence="daily")
    next_task = task.complete()
    assert next_task.due_date == date.today() + timedelta(days=1)


# ── conflict detection ────────────────────────────────────────────────────────

def test_two_tasks_at_exact_same_time_detected_as_overlap():
    """Two tasks starting at the same hour are flagged as overlapping."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t1 = Task(name="Walk", category="walk", duration=30, priority=3, preferred_hour=9)
    t2 = Task(name="Feed", category="feed", duration=20, priority=4, preferred_hour=9)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = make_scheduler([pet], time_available=300)
    _, _, overlaps = scheduler.generate_plan()

    assert len(overlaps) == 1
    overlap_tasks = [overlaps[0][0], overlaps[0][1]]
    assert t1 in overlap_tasks
    assert t2 in overlap_tasks


def test_overlapping_tasks_detected_when_one_starts_mid_other():
    """A task starting during another's window is caught as an overlap."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    # 09:00–10:00 and 09:30–10:30 overlap
    t1 = Task(name="Walk", category="walk", duration=60, priority=3, preferred_hour=9)
    t2 = Task(name="Feed", category="feed", duration=60, priority=3, preferred_hour=9)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = make_scheduler([pet], time_available=300)
    _, _, overlaps = scheduler.generate_plan()

    assert len(overlaps) >= 1


def test_non_overlapping_tasks_produce_no_conflicts():
    """Tasks with non-overlapping windows generate no overlap warnings."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    # 08:00–08:30 and 09:00–09:20 — clear gap
    t1 = Task(name="Walk", category="walk", duration=30, priority=3, preferred_hour=8)
    t2 = Task(name="Feed", category="feed", duration=20, priority=4, preferred_hour=9)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = make_scheduler([pet], time_available=300)
    _, _, overlaps = scheduler.generate_plan()

    assert overlaps == []


def test_tasks_without_preferred_hour_not_flagged_as_conflict():
    """Tasks with no preferred_hour are excluded from overlap detection."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t1 = Task(name="Walk", category="walk", duration=30, priority=3)
    t2 = Task(name="Feed", category="feed", duration=20, priority=4)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = make_scheduler([pet], time_available=300)
    _, _, overlaps = scheduler.generate_plan()

    assert overlaps == []


def test_overlap_warning_message_contains_task_names():
    """The overlap warning string identifies the conflicting task names."""
    pet = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    t1 = Task(name="Walk", category="walk", duration=60, priority=3, preferred_hour=9)
    t2 = Task(name="Feed", category="feed", duration=60, priority=4, preferred_hour=9)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = make_scheduler([pet], time_available=300)
    _, _, overlaps = scheduler.generate_plan()

    assert len(overlaps) == 1
    warning_msg = overlaps[0][2]
    assert "Walk" in warning_msg
    assert "Feed" in warning_msg
