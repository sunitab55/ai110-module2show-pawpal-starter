from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Task:
    name: str
    category: str  # walk, feed, meds, grooming, enrichment, etc.
    duration: int  # minutes
    priority: int  # 1 (low) to 5 (high)
    times_per_day: int = 1
    is_completed: bool = False
    preferred_hour: int | None = None  # 0–23; None means no time preference
    recurrence: str | None = None      # "daily", "weekly", or None
    due_date: date | None = None       # None means due today

    def complete(self) -> "Task | None":
        """Mark this task as completed and return the next occurrence if recurring.

        Returns a new Task with an updated due_date, or None for one-off tasks.
        """
        self.is_completed = True
        if self.recurrence == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
        else:
            return None
        return Task(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            times_per_day=self.times_per_day,
            preferred_hour=self.preferred_hour,
            recurrence=self.recurrence,
            due_date=next_due,
        )

    def to_dict(self) -> dict:
        """Return task data as a dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "duration": self.duration,
            "priority": self.priority,
            "times_per_day": self.times_per_day,
            "is_completed": self.is_completed,
            "preferred_hour": self.preferred_hour,
            "recurrence": self.recurrence,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self._tasks

    def complete_task(self, task: Task) -> "Task | None":
        """Mark a task complete and automatically add the next occurrence if recurring.

        Returns the newly created Task, or None for one-off tasks.
        """
        next_task = task.complete()
        if next_task:
            self._tasks.append(next_task)
        return next_task


@dataclass
class Owner:
    name: str
    time_available: int  # minutes per day
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's pet list."""
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self._pets


@dataclass
class Scheduler:
    owner: Owner

    @property
    def tasks(self) -> list[Task]:
        """Aggregate all tasks from all of the owner's pets."""
        return [task for pet in self.owner.get_pets() for task in pet.get_tasks()]

    def _priority_score(self, task: Task) -> int:
        """Compute the effective priority of a task.

        Adds a +1 bonus when the task's category appears in the owner's preferences
        list, breaking ties in favour of care types the owner has flagged as important.
        Raw priority range is 1–5; with the bonus the effective range is 1–6.
        """
        bonus = 1 if task.category in self.owner.preferences else 0
        return task.priority + bonus

    def _pet_for_task(self, task: Task):
        """Return the Pet that owns this task, or None if not found.

        Iterates every pet registered with the owner and returns the first one
        whose task list contains the given task. Used by conflict detection and
        overlap reporting to attach pet names to warning messages.
        """
        for pet in self.owner.get_pets():
            if task in pet.get_tasks():
                return pet
        return None

    def sort_by_priority(self) -> list[Task]:
        """Return all tasks sorted from highest to lowest effective priority.

        Effective priority is computed by _priority_score(), which adds a +1 bonus
        for tasks whose category matches an owner preference. Tasks not matching any
        preference are ranked purely by their raw priority value.
        """
        return sorted(self.tasks, key=self._priority_score, reverse=True)

    def _interleave_by_pet(self, sorted_tasks: list[Task]) -> list[Task]:
        """Re-order tasks so every pet gets one scheduling slot before any pet gets a second.

        Accepts a globally priority-sorted list and distributes tasks round-robin
        across pets: the top-priority task from pet 1, then pet 2, then pet 1's
        second task, and so on. Within each pet's slice the relative priority order
        from sorted_tasks is preserved.

        This prevents a pet with uniformly high-priority tasks from monopolising the
        time budget and leaving another pet with no scheduled care.
        """
        pets = self.owner.get_pets()
        pet_queues = {
            pet.name: [t for t in sorted_tasks if t in pet.get_tasks()]
            for pet in pets
        }
        interleaved = []
        max_len = max((len(q) for q in pet_queues.values()), default=0)
        for i in range(max_len):
            for pet in pets:
                queue = pet_queues[pet.name]
                if i < len(queue):
                    interleaved.append(queue[i])
        return interleaved

    def apply_constraints(self, ordered_tasks: list[Task]) -> tuple[list[Task], list[Task]]:
        """Filter tasks to fit within the owner's available daily time budget.

        Steps:
        1. Expands each task into times_per_day copies so recurring tasks (e.g.
           medication given twice a day) consume their full share of the budget.
        2. Skips any task already marked is_completed — no re-scheduling finished work.
        3. Greedily adds tasks to the schedule while total duration <= time_available.
        4. Passes each task that doesn't fit to _conflict_reason() so the caller
           knows whether the deferral was a plain budget overrun or a priority clash
           with a same-scored task from a different pet.

        Returns:
            scheduled: tasks that fit within the time budget, in the order provided.
            deferred:  list of (task, reason) tuples for tasks that were dropped.
        """
        expanded = [
            task
            for task in ordered_tasks
            if not task.is_completed
            for _ in range(task.times_per_day)
        ]

        scheduled = []
        deferred = []
        time_used = 0

        for task in expanded:
            if time_used + task.duration <= self.owner.time_available:
                scheduled.append(task)
                time_used += task.duration
            else:
                reason = self._conflict_reason(task, scheduled)
                deferred.append((task, reason))

        return scheduled, deferred

    def _conflict_reason(self, deferred_task: Task, scheduled: list[Task]) -> str:
        """Produce a human-readable reason explaining why a task was deferred.

        Checks whether any already-scheduled task from a *different* pet shares the
        same effective priority score as the deferred task. If so, the two tasks
        competed for the same scheduling position and one was squeezed out — this is
        reported as a named priority conflict so the owner can decide which pet's
        need to prioritise.

        Falls back to the generic "time budget exceeded" message when no same-priority
        cross-pet competitor is found.
        """
        deferred_score = self._priority_score(deferred_task)
        deferred_pet = self._pet_for_task(deferred_task)

        for other in scheduled:
            if self._priority_score(other) == deferred_score:
                other_pet = self._pet_for_task(other)
                if other_pet and deferred_pet and other_pet.name != deferred_pet.name:
                    return f"priority conflict with {other_pet.name}'s '{other.name}'"

        return "time budget exceeded"

    def sort_by_time(self, scheduled: list[Task]) -> list[Task]:
        """Order a list of scheduled tasks by preferred_hour ascending.

        Produces a clock-ordered daily schedule so the owner sees tasks in the
        sequence they should be performed. Tasks with no preferred_hour (None)
        have no fixed time and are placed at the end (treated as hour 24).
        """
        return sorted(scheduled, key=lambda t: t.preferred_hour if t.preferred_hour is not None else 24)

    def _detect_overlaps(self, scheduled: list[Task]) -> list[tuple[Task, Task, str]]:
        """Identify every pair of scheduled tasks whose time windows collide.

        Converts each task's preferred_hour and duration into a minute-level interval
        [start, end) and tests all pairs for intersection using the standard overlap
        condition: a.start < b.end and b.start < a.end.

        Tasks without a preferred_hour are excluded — their start time is unknown so
        overlap cannot be determined.

        Returns a list of (task_a, task_b, warning_message) triples. The warning
        message names both pets and tasks and shows the exact HH:MM windows so the
        owner can reschedule one of the conflicting tasks.
        """
        timed = [t for t in scheduled if t.preferred_hour is not None]
        overlaps = []
        for i, a in enumerate(timed):
            a_start = a.preferred_hour * 60
            a_end = a_start + a.duration
            for b in timed[i + 1:]:
                b_start = b.preferred_hour * 60
                b_end = b_start + b.duration
                if a_start < b_end and b_start < a_end:
                    pet_a = self._pet_for_task(a)
                    pet_b = self._pet_for_task(b)
                    label_a = f"{pet_a.name}'s '{a.name}'" if pet_a else f"'{a.name}'"
                    label_b = f"{pet_b.name}'s '{b.name}'" if pet_b else f"'{b.name}'"
                    msg = (
                        f"WARNING: {label_a} ({a.preferred_hour:02d}:00-{a_end // 60:02d}:{a_end % 60:02d}) "
                        f"overlaps with {label_b} ({b.preferred_hour:02d}:00-{b_end // 60:02d}:{b_end % 60:02d})"
                    )
                    overlaps.append((a, b, msg))
        return overlaps

    def generate_plan(self) -> tuple[list[Task], list[Task], list[tuple[Task, Task, str]]]:
        """Generate a complete, clock-ordered daily care plan for the owner.

        Pipeline:
        1. sort_by_priority()     — rank all tasks by effective priority (with
                                    owner-preference bonus).
        2. _interleave_by_pet()   — reorder so every pet gets one slot before any
                                    pet gets a second (fair representation).
        3. apply_constraints()    — greedily fill the time budget; deferred tasks
                                    carry a reason (budget or priority conflict).
        4. sort_by_time()         — order the scheduled tasks by preferred_hour so
                                    the plan reads as a real daily timeline.
        5. _detect_overlaps()     — scan for tasks whose time windows collide and
                                    return warnings for the owner to act on.

        Returns:
            scheduled: clock-ordered list of tasks that fit the day.
            deferred:  list of (task, reason) for tasks that were dropped.
            overlaps:  list of (task_a, task_b, warning_message) for time collisions.
        """
        sorted_tasks = self.sort_by_priority()
        ordered_tasks = self._interleave_by_pet(sorted_tasks)
        scheduled, deferred = self.apply_constraints(ordered_tasks)
        scheduled = self.sort_by_time(scheduled)
        overlaps = self._detect_overlaps(scheduled)
        return scheduled, deferred, overlaps
