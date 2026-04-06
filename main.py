from pawpal_system import Task, Pet, Owner, Scheduler

# Create owner
owner = Owner(name="Alex", time_available=120)

# Create pets
dooshtu = Pet(name="Dooshtu", species="Dog", breed="Husky", age=3)
booshtu = Pet(name="Booshtu", species="Cat", breed="Maine Coon", age=5)

# Add tasks to Dooshtu
dooshtu.add_task(Task(name="Morning Walk", category="walk", duration=30, priority=5, times_per_day=1))
dooshtu.add_task(Task(name="Breakfast", category="feed", duration=10, priority=4, times_per_day=1))
dooshtu.add_task(Task(name="Evening Walk", category="walk", duration=45, priority=5, times_per_day=1))

# Add tasks to Booshtu
booshtu.add_task(Task(name="Medication", category="meds", duration=5, priority=5, times_per_day=2))
booshtu.add_task(Task(name="Playtime", category="enrichment", duration=20, priority=3, times_per_day=1))
booshtu.add_task(Task(name="Grooming", category="grooming", duration=15, priority=2, times_per_day=1))

# Register pets with owner
owner.add_pet(dooshtu)
owner.add_pet(booshtu)

# Generate schedule
scheduler = Scheduler(owner=owner)
plan = scheduler.generate_plan()

# Print today's schedule
print("=== Today's Schedule ===\n")
for pet in owner.get_pets():
    pet_tasks = [t for t in plan if t in pet.get_tasks()]
    if pet_tasks:
        print(f"[{pet.name}]")
        for task in pet_tasks:
            status = "done" if task.is_completed else "pending"
            print(f"  - {task.name} ({task.category}, {task.duration} min, priority {task.priority}) [{status}]")
        print()

total = sum(t.duration for t in plan)
print(f"Total time: {total} min / {owner.time_available} min available")
