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
scheduler = Scheduler(owner)  # cheap wrapper; recreated each rerun around the persisted owner
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

# --- Tasks & Completion ---------------------------------------------------
# Surfaces the Scheduler's sorting/filtering, and lets the user complete a
# task -- which triggers Pet.complete_task() and auto-spawns the next
# occurrence for recurring tasks.
st.subheader("✅ Tasks & Completion")
if not owner.all_tasks():
    st.info("No tasks yet. Add some above to see them here.")
else:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.radio("Show", ["Pending", "Completed", "All"], horizontal=True)

    # Sort by time (Scheduler.sort_by_time) and filter by pet (filter_by_pet).
    if pet_filter == "All pets":
        tasks = scheduler.sort_by_time(owner.all_tasks())
    else:
        tasks = scheduler.sort_by_time(scheduler.filter_by_pet(pet_filter))

    if status_filter == "Pending":
        tasks = [t for t in tasks if not t.completed]
    elif status_filter == "Completed":
        tasks = [t for t in tasks if t.completed]

    if tasks:
        st.table(
            [
                {
                    "Time": t.fixed_time.strftime("%H:%M") if t.fixed_time else "flexible",
                    "Task": t.title,
                    "Priority": t.priority,
                    "Recurs": t.recurrence,
                    "Status": "✅ done" if t.completed else "⬜ pending",
                }
                for t in tasks
            ]
        )
    else:
        st.caption("No tasks match this filter.")

    # Completing a task advances recurring ones to their next occurrence.
    pending_pairs = [(pet, t) for pet in owner.pets for t in pet.tasks if not t.completed]
    if pending_pairs:
        with st.form("complete_form"):
            choice = st.selectbox(
                "Mark a task complete",
                range(len(pending_pairs)),
                format_func=lambda i: f"{pending_pairs[i][0].name}: {pending_pairs[i][1].title}",
            )
            if st.form_submit_button("Mark complete"):
                pet, task = pending_pairs[choice]
                follow_up = pet.complete_task(task)
                if follow_up is not None:
                    st.success(
                        f"Completed '{task.title}'. Next {task.recurrence} occurrence "
                        f"auto-scheduled for {follow_up.due_date}."
                    )
                else:
                    st.success(f"Completed '{task.title}'.")
                st.rerun()

st.divider()

# --- Generate Schedule ----------------------------------------------------
st.subheader("🗓️ Generate Schedule")
if st.button("Generate schedule", type="primary"):
    if not owner.all_tasks():
        st.warning("No tasks yet. Add some tasks first.")
    else:
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

            # A conflict is advisory, not fatal: show a non-blocking amber
            # warning with guidance rather than a red error, and confirm with
            # a green success when the day is clean.
            warnings = scheduler.conflict_warnings(plan)
            if warnings:
                st.warning(
                    "⚠️ Some tasks overlap. Fixed-time tasks aren't moved automatically — "
                    "consider adjusting one task in each pair below:"
                )
                for w in warnings:
                    st.markdown(f"- {w}")
            else:
                st.success("No scheduling conflicts. 🎉")

            with st.expander("Why this plan?"):
                st.text(scheduler.explain(plan))
