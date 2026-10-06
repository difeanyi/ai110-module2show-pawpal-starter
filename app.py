import datetime as dt

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

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

# --- Owner (kept in session_state so it survives reruns) ----------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.update_available_time(
        int(st.number_input("Minutes available today", min_value=0, max_value=1440,
                            value=owner.available_minutes, step=5))
    )

# --- Add a pet -> Owner.add_pet ----------------------------------------------

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        breed = st.text_input("Breed (optional)")
    with col4:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(name=pet_name.strip(), species=species, breed=breed.strip(), age=int(age)))
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as e:
                st.error(str(e))

if owner.pets:
    st.table([{"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age}
              for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

# --- Add a task -> Pet.add_task ----------------------------------------------

st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_pet = st.selectbox("For pet", [p.name for p in owner.pets])
            description = st.text_input("Task", value="Morning walk")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
            has_time = st.checkbox("Preferred start time?")
            preferred = st.time_input("Start time", value=dt.time(8, 0), step=900)
        if st.form_submit_button("Add task"):
            try:
                owner.get_pet(task_pet).add_task(Task(
                    description=description.strip() or "Untitled task",
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    time=preferred.strftime("%H:%M") if has_time else None,
                ))
                st.success(f"Added '{description}' for {task_pet}.")
            except ValueError as e:
                st.error(str(e))

    scheduler = Scheduler(owner)

    # --- Mark complete -> Scheduler.mark_task_complete (creates next daily/weekly occurrence) ---
    open_tasks = scheduler.sort_by_time(scheduler.get_tasks(completed=False))
    if open_tasks:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            choice = st.selectbox(
                "Mark a task complete",
                [(p.name, t.task_id) for p, t in open_tasks],
                format_func=lambda key: next(
                    f"{p.name}: {t.description}" + (f" ({t.time})" if t.time else "")
                    + (f" - due {t.due_date:%a %d %b}" if t.due_date else "")
                    for p, t in open_tasks if (p.name, t.task_id) == key
                ),
            )
        with col2:
            if st.button("Mark complete", width="stretch"):
                next_task = scheduler.mark_task_complete(*choice, on=dt.date.today())
                st.session_state.flash = (
                    f"Done! Next '{next_task.description}' is due {next_task.due_date:%a %d %b}."
                    if next_task else "Done!"
                )
                st.rerun()  # redraw so the dropdown and table reflect the change
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    # --- Task list view -> Scheduler.get_due_tasks / filter_tasks / sort_by_time / sort_tasks ---
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show", ["Due today", "Open", "Completed", "All"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Time", "Priority"])

    if status_filter == "Due today":
        pairs = scheduler.get_due_tasks(dt.date.today())
    else:
        pairs = scheduler.get_tasks(completed={"Open": False, "Completed": True, "All": None}[status_filter])
    pairs = scheduler.filter_tasks(pairs, pet_name=None if pet_filter == "All pets" else pet_filter)
    pairs = scheduler.sort_by_time(pairs) if sort_by == "Time" else scheduler.sort_tasks(pairs)

    rows = [{"Time": t.time or "-", "Pet": p.name, "Task": t.description, "Minutes": t.duration_minutes,
             "Priority": t.priority, "Frequency": t.frequency,
             "Due": f"{t.due_date:%a %d %b}" if t.due_date else "now",
             "Done": "✅" if t.completed else ""} for p, t in pairs]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    elif scheduler.get_tasks():
        st.info("No tasks match these filters.")
    else:
        st.info("No tasks yet. Add one above.")

    # --- Live conflict check -> Scheduler.detect_conflicts ---
    conflicts = scheduler.detect_conflicts(on=dt.date.today())
    if conflicts:
        st.warning(f"**{len(conflicts)} time conflict(s) today.** The schedule will move the later "
                   "task in each pair, or you can change a task's time.", icon="⚠️")
        for c in conflicts:
            st.caption(f"• {c}")
    elif scheduler.get_due_tasks(dt.date.today()):
        st.success("No time conflicts among today's tasks.", icon="✅")

st.divider()

# --- Build schedule -> Scheduler.generate_plan --------------------------------

st.subheader("Build Schedule")
start = st.time_input("Day starts at", value=dt.time(8, 0), step=900)

if st.button("Generate schedule"):
    plan = Scheduler(owner, start_time=start).generate_plan(dt.date.today())
    col1, col2, col3 = st.columns(3)
    col1.metric("Minutes scheduled", f"{plan.total_minutes} / {plan.available_minutes}")
    col2.metric("Tasks scheduled", len(plan.entries))
    col3.metric("Skipped", len(plan.skipped))

    for w in plan.warnings:
        st.warning(f"Time conflict: {w}", icon="⚠️")
    if plan.entries:
        st.dataframe([{"Time": f"{e.start:%H:%M}-{e.end:%H:%M}", "Pet": e.pet_name,
                       "Task": e.task.description, "Priority": e.task.priority, "Why": e.reason}
                      for e in plan.entries], hide_index=True, width="stretch")
    else:
        st.info("Nothing due today. Add tasks, or check back when recurring tasks come due.")
    if plan.skipped:
        st.markdown("**Skipped (not enough time)**")
        st.dataframe([{"Pet": s.pet_name, "Task": s.task.description, "Priority": s.task.priority,
                       "Why": s.reason} for s in plan.skipped], hide_index=True, width="stretch")
    with st.expander("Plain-text summary"):
        st.code(plan.summary(), language=None)
