# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
Interface you can add a pet/pets with a calender, stemming from the pets you can have many different needs, walk frequency, feeding times etc calender/pet can likely have blocked time areas where the owner is unavailable so those times are not chosen for walking.
Pet - Adding/Removing
Attributes - Animal - Breed - Medication - Food Requirments - Exercise Requirments
Calender - Notifications - Adding Events
Owner - Above Pets 
Logging Task that were completed


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Yeah it changed a bit. I had Claude review my skeleton to point out what relationships were missing before i got to far into it, and it flagged a couple things i hadnt thought about. The first was that my Owner just held the pets and the Calender was sort of floating on its own, but the scheduler needs the pets and the calender together and nothing said whose calender it was, so based on that i moved the Calender to live inside the Owner so it all comes from one place. The second thing it caught was that my Event only stored the type and the pet_id, so theres no way to trace an event back to which care need or priority it came from when i want to explain the plan, so i added a care_need_id onto the Event to fix that.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
The scheduler never books two things at the same time. Once it places a task, that time is taken, so the next task goes somewhere else. The catch is it only guarantees this for tasks it schedules. If an event gets added some other way, an overlap can happen. This works for the scenario because it's one owner who can only do one thing at a time, so auto avoiding overlaps is what they'd want anyway.

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
