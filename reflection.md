# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML has four classes, each with a single clear responsibility:

- **Owner** — represents the person planning care. Holds their name, their
  available time window (`available_start`/`available_end`), preferred task
  categories, and the list of pets they own. It can register a pet
  (`add_pet`) and gather every task across its pets (`all_tasks`).
- **Pet** — a dataclass holding a pet's `name`, `species`, `breed`, and the
  list of care `tasks` that belong to it. It can attach a task (`add_task`).
- **Task** — a dataclass for one unit of care work: `title`,
  `duration_minutes`, `priority`, `category`, `recurrence`, and an optional
  `fixed_time` for tasks that must happen at a set time. `priority_rank()`
  converts the priority label into a number so tasks can be sorted.
- **Scheduler** — the algorithm layer. It takes an Owner and turns their
  tasks plus constraints into an ordered daily plan (`build_plan`), with
  helpers to sort by priority (`sort_tasks`), expand recurring tasks
  (`expand_recurring`), detect time conflicts (`detect_conflicts`), and
  explain its choices (`explain`).

Relationships: an Owner *owns* many Pets, each Pet *has* many Tasks, and the
Scheduler *plans for* one Owner while *ordering* its Tasks. I kept data
(Owner/Pet/Task) separate from behavior (Scheduler) so the scheduling logic
can be tested independently of the UI.

**b. Design changes**

Yes. After asking my AI assistant to review the skeleton for missing
relationships and logic bottlenecks, I made two changes:

1. **Added a `ScheduledTask` class.** My original plan was just a
   `list[Task]`, but a raw `Task` only knows its *duration* and an optional
   `fixed_time` — it has no *assigned* start/end once it's placed on the
   day. That made it impossible to time-box the day or detect overlaps.
   `ScheduledTask` wraps a `Task` with a concrete `start`/`end` (and the
   `pet_name` for display), so a daily plan is now a `list[ScheduledTask]`.
   `build_plan`, `detect_conflicts`, and `explain` now use this type.

2. **Added a `weekday` field to `Task`.** `expand_recurring(tasks, day)` is
   meant to decide which recurring tasks are due on a given day, but a
   `weekly` task had no anchor telling it *which* weekday it recurs on. The
   optional `weekday` (0=Mon..6=Sun) makes weekly recurrence resolvable.

I updated `diagrams/uml.mmd` to match: it now shows `ScheduledTask` wrapping
`Task`, the `Scheduler ..> ScheduledTask : produces` relationship, and the
new `weekday` attribute.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

My `build_plan` uses **greedy earliest-fit placement**: it anchors fixed-time
tasks, then walks the flexible tasks in priority order and drops the ones that
no longer fit inside the owner's available window. The tradeoff is that it is
*not* an optimal packer -- it can drop a low-priority task even when a smarter
algorithm could have rearranged the day to squeeze it in.

This is reasonable for the scenario for three reasons: (1) a pet owner's day
has only a handful of tasks, so the difference between greedy and optimal is
usually zero; (2) greedy placement is predictable and easy to explain to the
user ("highest priority first, earliest free slot"), which matters more than
theoretical optimality for a trust-based planning tool; and (3) it degrades
gracefully -- when the day is over-full, it keeps the important tasks and drops
the least important, which is exactly what a busy owner would want.

A related tradeoff: for fixed-time overlaps the scheduler **detects and warns
rather than auto-resolving**. It will not silently move a task the owner pinned
to a specific time (e.g. medication at 08:00), because respecting the owner's
explicit intent is safer than an automatic reschedule. Notably, the overlap
check uses full duration ranges (`start < other.end and other.start < end`),
not just exact start-time matches, so a task starting mid-way through another
is still flagged.

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
