# Portfolio summary

## RouteCraft: GridCourier

RouteCraft is a small, self-contained reinforcement-learning environment for warehouse delivery. An agent must collect a parcel and deliver it while navigating generated walls, a limited move budget, and a moving hazard on the hardest task.

### What the project demonstrates

- A seeded environment with a clear `reset`/`step` interface and four difficulty levels.
- A breadth-first-search planner, random baseline, and memorized-route comparison.
- Outcome-based scoring on held-out seeds, with pickup milestones for the battery-limited stretch task.
- Reproducible demonstrations showing why a fixed route and local test edits do not establish task success.

On the recorded 20-seed evaluation split, the planner delivered on every easy, medium, and hard episode. It delivered on 8 of 20 stretch episodes and collected the parcel in all 20. These runs demonstrate a working environment and grader; the planner is not an RL-trained model.

### Project context

This is new portfolio work created for an assignment. OpenAI Codex assisted with implementation, experiment scripts, and documentation; details are recorded in [`AI_TOOLS.md`](AI_TOOLS.md). The project is intended to be presented with that disclosure and with a clear explanation of its evaluation limits.
