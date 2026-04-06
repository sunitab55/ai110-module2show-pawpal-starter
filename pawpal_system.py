from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str  # walk, feed, meds, grooming, enrichment, etc.
    duration: int  # minutes
    priority: int  # 1 (low) to 5 (high)
    is_completed: bool = False

    def complete(self):
        self.is_completed = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "duration": self.duration,
            "priority": self.priority,
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
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        return self._tasks


@dataclass
class Owner:
    name: str
    time_available: int  # minutes per day
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet):
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        return self._pets


@dataclass
class Scheduler:
    owner: Owner
    pet: Pet

    @property
    def tasks(self) -> list[Task]:
        return self.pet.get_tasks()

    def sort_by_priority(self) -> list[Task]:
        return sorted(self.tasks, key=lambda t: t.priority, reverse=True)

    def apply_constraints(self, sorted_tasks: list[Task]) -> list[Task]:
        scheduled = []
        time_used = 0
        for task in sorted_tasks:
            if time_used + task.duration <= self.owner.time_available:
                scheduled.append(task)
                time_used += task.duration
        return scheduled

    def generate_plan(self) -> list[Task]:
        sorted_tasks = self.sort_by_priority()
        return self.apply_constraints(sorted_tasks)