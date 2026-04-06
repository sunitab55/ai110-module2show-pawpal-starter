from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str  # walk, feed, meds, grooming, enrichment, etc.
    duration: int  # minutes
    priority: int  # 1 (low) to 5 (high)
    times_per_day: int = 1
    is_completed: bool = False

    def complete(self):
        """Mark this task as completed."""
        self.is_completed = True

    def to_dict(self) -> dict:
        """Return task data as a dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "duration": self.duration,
            "priority": self.priority,
            "times_per_day": self.times_per_day,
            "is_completed": self.is_completed,
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

    def sort_by_priority(self) -> list[Task]:
        """Return tasks sorted from highest to lowest priority."""
        return sorted(self.tasks, key=lambda t: t.priority, reverse=True)

    def apply_constraints(self, sorted_tasks: list[Task]) -> list[Task]:
        """Filter tasks to fit within the owner's available time."""
        scheduled = []
        time_used = 0
        for task in sorted_tasks:
            if time_used + task.duration <= self.owner.time_available:
                scheduled.append(task)
                time_used += task.duration
        return scheduled

    def generate_plan(self) -> list[Task]:
        """Generate a prioritized daily care plan within the owner's time constraints."""
        sorted_tasks = self.sort_by_priority()
        return self.apply_constraints(sorted_tasks)
