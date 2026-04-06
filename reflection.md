# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
I designed the system using five classes that separate the data (owner, pet, and tasks) from the logic (scheduling and planning). The Scheduler takes in the owner and pet information and produces a DailyPlan based on priorities and time constraints.
I designed the system around an Owner who owns one or more Pets, each with a list of Tasks (walks, feeding, meds, etc.) that have a duration and priority. I created a Scheduler class that takes the owner and pet as input, applies constraints like available time, and sorts tasks by priority to produce a DailyPlan. The DailyPlan stores both the scheduled and skipped tasks, along with a reasoning explanation for why I constructed the plan that way.
- What classes did you include, and what responsibilities did you assign to each?
I included the following classes:
- Owner: stores owner information and preferences.
- Pet: stores pet information and a list of care tasks.
- Task: represents a single care task with attributes like name, category, duration, and priority.
- Scheduler: contains the logic to generate a plan based on the owner and pet information.
Owner owns one or more Pets, each with a list of Tasks (walks, feeding, meds, etc.) that have a duration and priority. Scheduler uses the owner and pet information to create a plan!


**b. Design changes**

- Did your design change during implementation?
Yes. I added the Frequency attribute to the Task class that the initial UML design did not include.
- If yes, describe at least one change and why you made it.
I made this change thinking about my own experience as a cat owner. My cat enjoys small portions multiple times a day!
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
My scheduler considers the following constraints:
  - **Time budget**: tasks are only scheduled if they fit within the owner's `time_available` (minutes per day).
  - **Priority**: tasks are ranked by priority score (1–5), with a +1 bonus for categories matching the owner's preferences, so preferred care types rise to the top when priorities are otherwise equal.
  - **Task frequency**: each task is expanded by its `times_per_day` value before scheduling, so a medication due twice daily correctly occupies two slots in the day's budget.
  - **Completion status**: tasks already marked `is_completed` are skipped entirely and never re-scheduled.
- How did you decide which constraints mattered most?
Time budget is the hard constraint — it gates everything else. Within that gate, priority (plus the preference bonus) determines which tasks get in. Frequency and completion status are correctness concerns: without them, the schedule would either under-count recurring tasks or re-schedule finished ones.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The scheduler uses a greedy approach: it picks tasks in priority order and adds each one if it fits, moving on once the time budget is full. This means a single long high-priority task can block several shorter medium-priority tasks that together would deliver more value.
- Why is that tradeoff reasonable for this scenario?
For a daily pet care schedule, the highest-priority tasks (medications, essential walks) should always make the cut regardless of duration. A globally optimal packing algorithm would be harder to reason about and explain to a pet owner. The greedy approach is transparent: "I scheduled the most important things first."

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI tools for design brainstorming, especially to help me think through the class structure and responsibilities. I also used AI to generate test cases and to help me debug some of the scheduling logic when I was stuck.
- What kinds of prompts or questions were most helpful?
I was able to use prompts like "What classes would you create for a pet care scheduling system?" and "How would you implement a scheduling algorithm that prioritizes tasks based on time and importance?" to get useful suggestions for both design and implementation.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

- How did you evaluate or verify what the AI suggested?
I looked at the codebase and made sure the methods and classes made sense in the context of my existing design and suggestions.

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

