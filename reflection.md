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

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
