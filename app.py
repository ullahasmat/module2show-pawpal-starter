from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session memory -------------------------------------------------------
# Streamlit reruns this whole script top-to-bottom on every click, so any
# object we want to keep (the Owner and their pets) must live in
# st.session_state -- the "vault" that persists across reruns. Check whether
# the Owner already exists before creating a fresh (empty) one, otherwise it
# would be reborn empty on every interaction.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_start=time(7, 0),
        available_end=time(20, 0),
    )

owner: Owner = st.session_state.owner
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

st.title("🐾 PawPal+")
st.caption("Add your pets and their care tasks, then generate a daily schedule.")

# --- Owner settings (sidebar) --------------------------------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    st.markdown("**Available window**")
    owner.available_start = st.time_input("Day starts", value=owner.available_start)
    owner.available_end = st.time_input("Day ends", value=owner.available_end)

    if st.button("Reset (clear pets & tasks)"):
        del st.session_state.owner
        st.rerun()

# --- Add a Pet ------------------------------------------------------------
st.subheader("🐕 Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        pet_name = st.text_input("Name")
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with c3:
        breed = st.text_input("Breed (optional)")

    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            # Owner.add_pet() handles the data -> a real Pet object joins the
            # owner that lives in session_state, so it persists across reruns.
            owner.add_pet(Pet(name=pet_name.strip(), species=species, breed=breed.strip()))
            st.success(f"Added {pet_name.strip()} to {owner.name}'s pets.")
        else:
            st.error("Please enter a pet name.")

if owner.pets:
    st.write("**Current pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species}) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a Task -----------------------------------------------------------
st.subheader("📋 Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        target_pet = st.selectbox("For which pet?", [p.name for p in owner.pets])
        task_title = st.text_input("Task title", value="Morning walk")

        c1, c2 = st.columns(2)
        with c1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with c2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        c3, c4 = st.columns(2)
        with c3:
            category = st.text_input("Category", value="general")
        with c4:
            recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])

        c5, c6 = st.columns(2)
        with c5:
            use_fixed = st.checkbox("Has a fixed start time?")
            fixed_time = st.time_input("Fixed time", value=time(8, 0))
        with c6:
            weekday_label = st.selectbox("Weekly on (weekly tasks only)", ["(any day)"] + WEEKDAYS)

        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == target_pet)
            weekday = None if weekday_label == "(any day)" else WEEKDAYS.index(weekday_label)
            pet.add_task(
                Task(
                    title=task_title.strip() or "Untitled task",
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category.strip() or "general",
                    recurrence=recurrence,
                    fixed_time=fixed_time if use_fixed else None,
                    weekday=weekday,
                )
            )
            st.success(f"Added '{task_title.strip()}' to {target_pet}.")

st.divider()

# --- Generate Schedule ----------------------------------------------------
st.subheader("🗓️ Generate Schedule")
if st.button("Generate schedule", type="primary"):
    if not owner.all_tasks():
        st.warning("No tasks yet. Add some tasks first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.build_plan(date.today())

        if not plan:
            st.warning("Nothing fit inside the available window. Try widening it in the sidebar.")
        else:
            st.table(
                [
                    {
                        "Start": s.start.strftime("%H:%M"),
                        "End": s.end.strftime("%H:%M"),
                        "Task": s.task.title,
                        "Pet": s.pet_name,
                        "Priority": s.task.priority,
                        "Fixed": "✓" if s.task.fixed_time else "",
                    }
                    for s in plan
                ]
            )

            for warning in scheduler.conflict_warnings(plan):
                st.error(f"⚠️ {warning}")

            with st.expander("Why this plan?"):
                st.text(scheduler.explain(plan))
