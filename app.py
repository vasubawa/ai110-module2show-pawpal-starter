import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
import uuid

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

# Persist an Owner object in Streamlit's session_state so it survives refreshes.
# Check if 'owner' exists; if not, create and store one. Update name if changed.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_id="owner_1", name=owner_name)
else:
    # keep owner object but update name if user changed the input
    if st.session_state.owner.name != owner_name:
        st.session_state.owner.name = owner_name

# Allow adding a pet to the owner
if st.button("Add pet"):
    new_pet = Pet(pet_id=str(uuid.uuid4()), name=pet_name, species=species, owner_id=st.session_state.owner.owner_id)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added pet {pet_name}")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# Pet selector for assigning tasks
pet_names = [p.name for p in st.session_state.owner.pets] if st.session_state.owner.pets else []
selected_pet = None
if pet_names:
    selected_pet = st.selectbox("Assign to pet", pet_names)

if st.button("Add task"):
    # map priority to numeric
    pri_map = {"low": 1, "medium": 5, "high": 9}
    pri = pri_map.get(priority, 5)
    task_obj = Task(task_id=str(uuid.uuid4()), title=task_title, duration_minutes=int(duration), priority=pri)
    st.session_state.tasks.append({"title": task_title, "duration_minutes": int(duration), "priority": priority})
    if selected_pet:
        pet_obj = next((p for p in st.session_state.owner.pets if p.name == selected_pet), None)
        if pet_obj:
            pet_obj.add_task(task_obj)
            st.success(f"Added task '{task_title}' to {pet_obj.name}")
        else:
            st.error("Selected pet not found")
    else:
        st.warning("No pet selected — task saved to session but not attached to a pet.")

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    scheduler = Scheduler()
    today = __import__("datetime").date.today()
    plan = scheduler.generate_daily_plan(owner, today)
    st.subheader("Today's Plan")
    st.text(scheduler.explain_plan(plan))
