from pawpal_system import Task, Pet


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
