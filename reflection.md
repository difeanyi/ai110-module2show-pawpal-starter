# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. **Add a pet and owner profile.** The user enters basic information about themselves (name, how much time they have each day, any preferences) and about their pet (name, species/breed, age). This gives the app the context it needs to plan care for that specific pet.
2. **Add and manage care tasks.** The user creates care tasks for their pet, such as a morning walk, feeding, giving medication, grooming or playtime. Each task has at least a duration and a priority, and the user can edit or remove tasks as the pet's needs change.
3. **Generate and view today's plan.** The user asks the app to build a daily schedule. The app orders and fits tasks within the owner's available time based on priority and preferences, then shows the plan clearly along with a short explanation of why it chose that order and why any tasks were left out.

**a. Initial design**

**Main objects, their attributes and methods**

**Owner**: the person caring for the pet.
- *Attributes:* `name`, `available_minutes` (time free for pet care today), `preferences` (e.g. prefers walks in the morning), `pets` (list of Pet)
- *Methods:* `add_pet(pet)`, `remove_pet(pet)`, `update_available_time(minutes)`, `set_preference(key, value)`

**Pet**: the animal being cared for.
- *Attributes:* `name`, `species`, `breed`, `age`, `tasks` (list of Task)
- *Methods:* `add_task(task)`, `edit_task(task_id, ...)`, `remove_task(task_id)`, `get_tasks()`

**Task**: a single care activity, such as a walk, feeding or medication.
- *Attributes:* `title`, `category` (walk, feeding, meds, grooming, enrichment), `duration_minutes`, `priority` (low / medium / high), `preferred_time` (optional, e.g. morning), `frequency` (daily, weekly), `completed`
- *Methods:* `mark_complete()`, `update(duration, priority, ...)`, `priority_score()` (turns priority into a number for sorting)

**Scheduler**: the logic that builds the daily plan.
- *Attributes:* `owner`, `pet`, `start_time` (when the day's plan begins)
- *Methods:* `sort_tasks()` (by priority, then duration), `fits_in_time(task, remaining_minutes)`, `generate_plan()` (returns a DailyPlan), `explain_choice(task)` (gives the reason a task was included or skipped)

**DailyPlan**: the result shown to the user.
- *Attributes:* `date`, `scheduled_tasks` (task + start time pairs), `skipped_tasks`, `total_minutes`, `reasons` (explanation for each decision)
- *Methods:* `add_entry(task, start_time, reason)`, `add_skipped(task, reason)`, `summary()` (returns readable text for the UI)

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design has five classes. I split them so that the data (who the owner is, what pets they have and what needs doing) is kept separate from the logic that decides the schedule and from the finished schedule itself.

- **Owner** holds the constraints for the day: how many minutes the owner has for pet care and their preferences, such as walking the dog in the morning. It also keeps the list of pets the owner is responsible for.
- **Pet** describes one animal and owns its list of care tasks. It is responsible for adding, editing and removing those tasks.
- **Task** is one care activity, with a duration, a priority, an optional preferred time and how often it repeats. It can mark itself complete and convert its priority into a number so the scheduler can sort tasks easily.
- **Scheduler** is the "brain" of the system. It reads the owner's constraints and the pet's tasks, sorts the tasks by priority, checks which ones fit in the available time, and builds the plan. It also explains why each task was included or skipped.
- **DailyPlan** is the output. It stores which tasks were scheduled and when, which were skipped, the total time used and the reason for each decision, and it can produce a readable summary for the Streamlit UI.

The relationships are: an Owner has one or more Pets, each Pet has many Tasks, and the Scheduler uses an Owner and a Pet to create a DailyPlan. I made Task, Pet, Owner and DailyPlan Python dataclasses because they mainly hold data, and kept Scheduler as a regular class because it mainly holds behavior.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, my design changed in a few important ways once I started implementing and reviewing it.

**Main change: the Scheduler now plans for the owner, not for one pet.** In my initial UML, the Scheduler took an `Owner` and a single `Pet`. When I reviewed the skeleton, I realised this was a problem: the owner's available minutes are shared between all of their pets, so scheduling each pet separately could give two dogs the full 60 minutes each and double-book the owner. I changed the Scheduler to take only the `Owner` and reach every pet through `owner.get_all_tasks()`. This one change is also what made later features possible, like filtering tasks by pet and detecting time conflicts between different pets.

**Other changes:**

- **The plan stores entries, not just tasks.** Initially `DailyPlan` held a plain list of tasks plus a separate dictionary of reasons. Once tasks came from several pets, a line like "Walk – 20 min" didn't say *which* pet. I added two small classes, `ScheduledTask` and `SkippedTask`, that each hold the pet name, the task, the time slot and the reason together.
- **I removed `explain_choice()`.** The reason a task is kept or skipped is only really known while `generate_plan()` is making the decision. A separate method would have had to repeat that logic and could give a different answer, so now the reason is recorded at the moment of the decision.
- **Recurring tasks became their own instances.** At first a daily task was one object checked against its `last_completed` date. Later I changed it so that completing a daily or weekly task creates a new copy with a `due_date` (`Task.next_occurrence()` called from `Pet.complete_task()`). This keeps a history of completed tasks and makes "what's due today" a simple check.
- **Smaller fixes:** I added a `task_id` so tasks can be edited and removed reliably, renamed `title`/`preferred_time` to `description`/`time` to match the assignment, and made `remove_pet` take a name to match how `remove_task` takes an id.

I updated `diagrams/uml.mmd` to match the final code, including arrows showing how completing a task flows from `Scheduler` → `Pet` → `Task` to create the next occurrence.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers these constraints:

- **Time budget:** the owner's available minutes for the day. A task is only included if it fits in the minutes that are left.
- **Priority:** high, medium or low. This decides which tasks are chosen first when time is limited.
- **Duration:** within the same priority, shorter tasks are chosen first so more care fits into the day.
- **Preferred start time:** tasks with a time like `08:15` are placed at that time, or as soon after as possible if the slot is taken.
- **Due date and completion:** only tasks that are not completed and are due today are scheduled. This is what keeps tomorrow's copy of a daily task out of today's plan.
- **No overlaps:** the owner can only do one thing at a time, so overlapping tasks are flagged as conflicts and the later one is moved.

I decided that **time and priority matter most**, because they reflect the real situation of a busy owner: there is a fixed amount of time, and some care (medication, feeding) is much more important than other care (extra playtime). If there isn't enough time, it is better to skip a low-priority task than a high-priority one. Preferred times come next, because they make the plan realistic, but they are treated as preferences rather than hard rules: if two tasks want the same slot, one is moved instead of being dropped.

The `Owner` class also stores general `preferences` (for example "walks in the morning"), but the scheduler does not use them yet. I chose to focus on the per-task preferred time instead, because it is more precise and easier to test.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: greedy, priority-first selection instead of finding the "best" combination of tasks.**

When choosing which tasks to include, my scheduler sorts the due tasks by priority (high first, then shortest first) and walks down the list once, keeping each task that still fits in the owner's remaining minutes. It never goes back to reconsider a choice. This means it does not always use the available time as fully as possible. For example, in my demo the owner has 120 minutes. After the high and medium priority tasks are placed, 20 minutes are left, so the 45-minute "Fetch in the yard" task is skipped and those 20 minutes go unused. A smarter algorithm (like the knapsack problem) could search every combination of tasks to fill the time as completely as possible, or to maximise total "priority points".

I think this tradeoff is reasonable for a pet care app because:

- **Important care comes first, every time.** A high-priority task like medication or feeding is never dropped just to fit in two low-priority tasks that happen to use the time better. For pet care, missing meds is much worse than having a few spare minutes.
- **The result is easy to explain.** Every skipped task gets a simple reason ("needs 45 min but only 20 min left"), which the user can understand and act on, for example by freeing up more time or lowering the task's duration. An optimal search would be harder to explain.
- **It's fast and simple.** An owner will only have a handful of tasks per day, so the extra complexity of an optimal search would add a lot of code for very little real benefit.

The downside is that the plan can leave small gaps of unused time. If that became a problem, a simple improvement would be a second pass that tries to fill the leftover minutes with any skipped tasks that are short enough.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used an AI coding assistant (Claude Code in VS Code) throughout the project, in roughly the same order as the project phases:

- **Design brainstorming:** turning the scenario into three core user actions, then into classes with attributes and methods, and then into a Mermaid UML diagram.
- **Scaffolding:** generating the class skeleton in `pawpal_system.py` with dataclasses, before writing any logic.
- **Design review:** asking it to review the skeleton for missing relationships and logic bottlenecks. This was one of the most useful steps, because it found problems before they were built into the code.
- **Implementation:** filling in the classes, then adding one algorithm at a time (sorting, filtering, recurring tasks, conflict detection), each with tests.
- **Debugging and environment help:** for example, why `python main.py` didn't work (macOS only has `python3`), and why `git add` failed when I ran it from the wrong folder.
- **UI and documentation:** connecting the classes to Streamlit with `st.session_state`, writing docstrings, and drafting README sections.

The most helpful prompts were **specific and scoped to one feature**, and named the class or method involved, for example "add logic to Task or Scheduler so that when a daily or weekly task is marked complete, a new instance is created", or "detect if two tasks are scheduled at the same time and return a warning instead of crashing". Prompts that asked for a **review or a check** ("does the UML still match the code?", "what's missing from this skeleton?") were also very useful, because they made the AI look for problems instead of just producing more code.

**Most effective assistant features for building the scheduler:**

- **Working directly in the project files.** The assistant could read `pawpal_system.py`, `app.py` and the tests and edit them in place, so its suggestions fit my existing code instead of being generic examples.
- **Running code to check its own work.** It ran `main.py`, `pytest` and a headless Streamlit test after changes. Several bugs were found this way rather than by me reading code.
- **Keeping the docs in sync.** When the code changed, it also updated the UML diagram, the README and the tests, which helped my documentation match the final implementation.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**Example 1: the Scheduler design.** The first skeleton the AI generated from my UML had `Scheduler(owner, pet)`, so it planned for one pet at a time. When I asked it to review the skeleton, it pointed out that the owner's time is shared between all pets, so scheduling each pet separately could double-book the owner. I did not keep the original version: I changed the Scheduler to take only the `Owner` and work across all pets. I also removed the suggested `explain_choice()` method, because it would have repeated the decision logic from `generate_plan()`; now the reason is recorded at the moment each decision is made. These changes kept the design simpler and made later features (filtering by pet, conflicts between pets) much easier.

**Example 2: sorting by time.** The first version of `sort_by_time()` sorted the `"HH:MM"` strings directly, which looked correct. When I asked how to sort times with a lambda key, the explanation pointed out that string sorting only works if every time has a leading zero, and a quick test showed that `"9:00"` was sorted after `"10:00"`. I modified the approach to sort by real `time` objects and to store times zero-padded, instead of accepting the simpler string version.

**How I verified suggestions:**

- **Running the code**, not just reading it: `python main.py` to see the real schedule, and `pytest` after every feature (14 tests by the end).
- **Testing edge cases on purpose**, such as unpadded times, completing a task twice, back-to-back tasks that should *not* count as conflicts, and two tasks at exactly the same time.
- **Checking explanations against real output.** For example, a draft of the README walkthrough said one task would stay at 08:00, but running the same tasks through the scheduler showed the shorter task actually goes first, so the README was corrected.
- **Comparing the UML diagram to the code** at the end to make sure every class, method and relationship matched.

**Keeping work organized by phase.** I worked through the project in clear phases (design and UML, class skeleton, core implementation, smarter scheduling algorithms, Streamlit UI, then documentation and reflection) and gave each phase its own focused requests. Keeping each phase separate meant every conversation had a single goal and the context stayed relevant: design discussions weren't mixed up with debugging, and each phase ended with something I could check (a diagram, passing tests, a working demo) before moving on. It also made it easy to go back and see why a decision was made at a certain step.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

My test suite (`tests/test_pawpal.py`) has 14 tests that cover:

- **Task basics:** `mark_complete()` changes a task's status and records the date, and adding a task increases the pet's task count.
- **Filtering:** by pet name, by completion status, by both together, and with a pet name that doesn't exist.
- **Recurring tasks:** completing a daily task creates a copy due the next day with the same details and a new id; a weekly task is due 7 days later and not a day early; a "once" task creates nothing; completing the same task twice doesn't create a duplicate; and the new copy is not scheduled until its due date.
- **Conflict detection:** two tasks at the same time for different pets, overlapping tasks for the same pet, back-to-back and untimed tasks that should *not* be flagged, and a generated plan that includes the warning but never has two tasks in the same slot.

These tests were important because the scheduling features interact with each other. For example, recurrence creates new tasks that the planner and conflict checker must then handle correctly. Each time I added a feature, running the whole suite showed that the earlier features still worked. The edge-case tests (back-to-back tasks, double completion) check the exact places where a small mistake would be easy to make and hard to notice by just looking at the output.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am **fairly confident (about 4 out of 5)** that the scheduler works correctly for normal daily use. All 14 tests pass, the `main.py` demo produces the plan I expect, and I tested the Streamlit flow (adding pets and tasks, completing a task, generating a plan) without errors. I'm less confident about unusual inputs, because the placement logic in `generate_plan()` is the most complex part and has fewer direct tests than the other features.

Edge cases I would test next:

- **Plans that run past midnight:** times currently wrap around to the start of the day.
- **Zero available minutes,** or a single task longer than the whole time budget.
- **A preferred time earlier than the day's start time**, and many timed tasks all wanting the same slot.
- **Completing a weekly task late**, to confirm the next due date is counted from the completion day.
- **Editing a task into an invalid state** (for example a negative duration through `edit_task`).
- **More detailed tests of `generate_plan()` placement**, checking that untimed tasks fill gaps correctly between timed tasks.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how the **scheduler explains itself**. Every task in the plan has a reason ("high priority, preferred 08:15", "moved to 08:20"), every skipped task says why ("needs 45 min but only 20 min left"), and overlapping tasks produce clear warnings instead of crashing. This matches the original goal of the app, which was not just to make a plan but to explain *why* it chose that plan. I'm also happy that the recurring tasks feature works end to end, from the class logic to the "Mark complete" button in the Streamlit app.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Use the owner's general preferences** (such as "walks in the morning") in the scheduler. They are stored but not used yet.
- **Fill leftover time with a second pass.** The greedy approach can leave unused minutes, so a second pass could fit in short skipped tasks.
- **Save data between sessions.** Everything is stored in `st.session_state`, so refreshing the page loses all pets and tasks. Saving to a JSON file would fix this.
- **Edit and delete tasks in the UI.** The methods exist in the `Pet` class, but the Streamlit app only lets you add and complete tasks.
- **Let the user choose how to resolve conflicts**, instead of always moving the later task.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that **I have to stay the "lead architect" when working with a powerful AI tool.** The AI can write a lot of correct-looking code very quickly, but correct-looking is not the same as correct, and fast is not the same as well designed. The biggest improvements in my project came from moments where I stepped back and checked the design rather than asking for more code: reviewing the skeleton before implementing it caught the one-pet Scheduler problem, and testing an unusual input caught the time-sorting bug.

Being the lead architect meant:

- **Deciding the structure first** (user actions, classes, UML) and using the AI to fill it in, not letting it decide the design.
- **Breaking the work into small, focused requests**, one feature at a time, so each change was easy to understand and test.
- **Verifying everything** by running the code and tests instead of trusting explanations.
- **Keeping the documentation honest**, so the UML, README and reflection describe what the code actually does.

The AI was most useful as a fast collaborator and reviewer, but I was responsible for the final decisions and for making sure the system made sense as a whole.
