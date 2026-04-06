import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Check the session_state "vault" before creating a new Owner/Pet.
# st.session_state persists across reruns, so we only instantiate once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, time_available=120)

if "pet" not in st.session_state:
    st.session_state.pet = Pet(name=pet_name, species=species, breed="unknown", age=0)
    st.session_state.owner.add_pet(st.session_state.pet)

st.markdown("### Tasks")

PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    category = st.text_input("Category", value="walk")
with col3:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col4:
    priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    new_task = Task(
        name=task_title,
        category=category,
        duration=int(duration),
        priority=PRIORITY_MAP[priority_label],
    )
    st.session_state.pet.add_task(new_task)

pet_tasks = st.session_state.pet.get_tasks()
if pet_tasks:
    st.write("Current tasks:")
    st.table([t.to_dict() for t in pet_tasks])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner=st.session_state.owner)
    scheduled, deferred, overlaps = scheduler.generate_plan()
    if scheduled:
        st.success(f"Scheduled {len(scheduled)} task(s):")
        st.table([t.to_dict() for t in scheduled])
    else:
        st.warning("No tasks fit within the available time. Add tasks or increase time available.")

    if overlaps:
        st.subheader("⚠️ Scheduling conflicts")
        for _, _, msg in overlaps:
            st.warning(msg)

    if deferred:
        st.subheader("Deferred tasks")
        st.table([{"name": t.name, "category": t.category, "duration": t.duration, "reason": reason} for t, reason in deferred])
