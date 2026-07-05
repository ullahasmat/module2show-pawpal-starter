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

My scheduler considers four constraints:

1. **The owner's available window** (`available_start`/`available_end`) -- the
   hard boundary a plan must fit inside.
2. **Task priority** (low / medium / high) -- the main driver of ordering.
3. **Fixed times** -- some tasks (e.g. 08:00 medication) must happen at an exact
   time and are treated as immovable anchors.
4. **Duration** -- used both to place tasks and as a tiebreaker between equal
   priorities (shorter first).
5. **Recurrence** -- daily/weekly tasks only appear on the days they are due.

I decided fixed times mattered most, then priority. A fixed time is a promise
the owner made (a vet appointment, a medication dose), so it is placed first and
never moved. Everything else flexes around those anchors, ordered by priority so
that if the day runs out of room, the least important tasks are the ones
dropped. Preferences like `preferred_categories` exist on the Owner but I chose
not to let them override priority -- keeping the ordering rule simple and
predictable was more valuable than a more nuanced but harder-to-explain scheme.

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

I used my AI coding assistant across every phase: brainstorming the UML and
class responsibilities, scaffolding the class skeleton from that UML,
implementing the scheduling algorithms (greedy placement, recurrence,
conflict detection), generating the pytest suite, and drafting documentation.

The most effective features were:

- **Agent / multi-file editing** for scaffolding and refactors -- generating the
  dataclass skeleton and later wiring `app.py` to the logic layer in one pass.
- **Attaching a file and asking for a critique**, e.g. "review this skeleton for
  missing relationships or logic bottlenecks." That surfaced the two best design
  changes I made: adding a `ScheduledTask` class (a plan needs assigned
  start/end times, not raw tasks) and a `weekday` anchor for weekly recurrence.
- **Running the CLI demo and pytest to verify behavior**, not just reading the
  code. Seeing `main.py` actually print a plan -- and later 15 green tests --
  was how I trusted each change.

The most helpful prompts were specific and grounded in my files: "how should the
Scheduler retrieve tasks from the Owner's pets?" and "what are the most important
edge cases to test for a scheduler with sorting and recurring tasks?"

**Using separate chat sessions per phase** (e.g. a fresh session for algorithmic
planning, another focused only on testing) kept each conversation's context
narrow. The testing chat stayed focused on edge cases instead of drifting back
into implementation details, which made its suggestions sharper and easier to
act on.

**b. Judgment and verification**

The clearest example of not accepting a suggestion as-is was `sort_by_time()`.
The assistant's first idea assumed task times were stored as `"HH:MM"` **strings**
and suggested parsing them in the sort key. My model stores times as
`datetime.time` objects with `None` for flexible tasks, so string parsing would
have been both fragile and wrong. I kept my stronger type and instead used a
tuple sort key -- `(fixed_time is None, minutes, -priority)` -- that pushes
untimed tasks to the end without any parsing. I made a similar call on
`detect_conflicts()`: I rejected a "more Pythonic" one-line comprehension and a
faster sweep-line rewrite, because for a handful of daily tasks the readable
pairwise version is clearer and the performance difference is unmeasurable.

I verified AI suggestions two ways: by running `main.py` and reading the actual
output (e.g. confirming a completed daily task spawned a copy due the *next*
day), and by writing tests that pin the behavior -- including a boundary test
that two tasks touching at 08:30 are **not** flagged as a conflict, which guards
the strict `<` comparison in the overlap check.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 15 pytest cases covering the four algorithms plus edge cases:

- **Sorting** -- `sort_by_time` returns timed tasks chronologically with flexible
  tasks last; `sort_tasks` orders by priority.
- **Filtering** -- `filter_by_pet` (including an unknown-pet name returning an
  empty list) and `filter_by_status` excluding completed tasks.
- **Recurrence** -- completing a daily task spawns a copy due the next day, a
  weekly task advances +7 days, a non-recurring task returns `None`, and a
  weekly task only appears on its weekday.
- **Conflict detection** -- two tasks at the same time are flagged, but two tasks
  that merely touch at a boundary are not.
- **Planning edge cases** -- an owner with no tasks yields an empty plan, and a
  task too long for the available window is dropped.

These mattered because the scheduler's bugs would be *silent*: a wrong sort or a
missed conflict still produces a plausible-looking plan, so only tests catch it.
I deliberately set explicit `due_date` values in the recurrence tests so they do
not depend on the real "today" and stay deterministic.

**b. Confidence**

I am fairly confident -- about **4 out of 5**. The core behaviors are covered by
passing happy-path and edge-case tests, and I verified the whole system end to
end through the CLI demo and the Streamlit UI. I held back the last point because
a few areas are still untested: packing several *flexible* tasks around multiple
fixed anchors, invalid input (e.g. an unknown priority string), and cross-pet
conflicts specifically. Those are the first cases I would add next.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the clean separation between data and behavior. The
`Owner`, `Pet`, and `Task` dataclasses hold state, and the `Scheduler` holds all
the algorithms. Because the scheduler has no UI dependencies, I could build and
verify the entire "brain" from a plain CLI script before touching Streamlit, and
I could unit-test every algorithm in isolation. The `explain()` method is a
close second -- having the system articulate *why* it made each choice made the
whole thing feel trustworthy rather than magic.

**b. What you would improve**

I would reconcile my two recurrence mechanisms. `expand_recurring()` treats
recurring tasks as templates that appear on matching days, while
`complete_task()` spawns a concrete dated next occurrence. They coexist because
`build_plan` skips completed tasks, but a single due-date-driven model would be
cleaner and would stop completed-task history from accumulating. I would also
add input validation (an unknown priority string currently ranks as 0 instead of
raising) and a smarter placement pass that can repack flexible tasks around
anchors rather than dropping them greedily.

**c. Key takeaway**

The biggest lesson was what being the **lead architect** actually means when
working with a powerful AI. The assistant could generate code faster than I could
type, but the value I added was judgment: deciding where constraints should live,
choosing to detect conflicts rather than auto-resolve them, keeping a readable
algorithm over a "cleverer" one, and insisting that every suggestion be verified
by a demo run or a test before I trusted it. The AI is an excellent implementer
and a tireless reviewer, but the design decisions -- and the responsibility for
whether the system is actually correct -- stayed with me. Treating the AI as a
collaborator I direct and check, rather than an oracle I obey, is what kept the
final system coherent.
