from pawpal_system import Task, Pet, Owner, Scheduler

# Create owner
owner = Owner(name="Alex", time_available=120)

# Create pets
dooshtu = Pet(name="Dooshtu", species="Dog", breed="Husky", age=3)
booshtu = Pet(name="Booshtu", species="Cat", breed="Maine Coon", age=5)

# Add tasks to Dooshtu
dooshtu.add_task(Task(name="Morning Walk", category="walk", duration=30, priority=5, times_per_day=1, preferred_hour=7))
dooshtu.add_task(Task(name="Breakfast", category="feed", duration=10, priority=4, times_per_day=1, preferred_hour=8))
dooshtu.add_task(Task(name="Evening Walk", category="walk", duration=45, priority=5, times_per_day=1, preferred_hour=18))

# Add tasks to Booshtu
# Medication at 07:00 overlaps with Dooshtu's Morning Walk (07:00–07:30)
# Feeding at 08:00 overlaps with Dooshtu's Breakfast (08:00–08:10)
booshtu.add_task(Task(name="Medication", category="meds", duration=5, priority=5, times_per_day=2, preferred_hour=7))
booshtu.add_task(Task(name="Feeding", category="feed", duration=15, priority=4, times_per_day=1, preferred_hour=8))
booshtu.add_task(Task(name="Playtime", category="enrichment", duration=20, priority=3, times_per_day=1, preferred_hour=15))
booshtu.add_task(Task(name="Grooming", category="grooming", duration=15, priority=2, times_per_day=1, preferred_hour=None))

# Register pets with owner
owner.add_pet(dooshtu)
owner.add_pet(booshtu)

# Generate schedule
scheduler = Scheduler(owner=owner)
scheduled, deferred, overlaps = scheduler.generate_plan()

# Print today's schedule
print("=== Today's Schedule ===\n")
for pet in owner.get_pets():
    pet_tasks = [t for t in scheduled if t in pet.get_tasks()]
    if pet_tasks:
        print(f"[{pet.name}]")
        for task in pet_tasks:
            status = "done" if task.is_completed else "pending"
            print(f"  - {task.name} ({task.category}, {task.duration} min, priority {task.priority}) [{status}]")
        print()

total = sum(t.duration for t in scheduled)
print(f"Total time: {total} min / {owner.time_available} min available")

if overlaps:
    print("\n=== Scheduling Conflicts ===\n")
    for _, _, msg in overlaps:
        print(f"  {msg}")

if deferred:
    print("\n=== Deferred Tasks ===\n")
    for task, reason in deferred:
        print(f"  - {task.name} ({task.duration} min): {reason}")
