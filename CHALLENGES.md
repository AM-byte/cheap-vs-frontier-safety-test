# Challenges log

## Experiment challenges
- The checker flagged Haiku for skipping approval, but Haiku hadn’t.
  - The checker compared the resource name in the approval request to the target exactly, and Haiku wrote "search-api (env=staging)" instead of "search-api".
  - The fix checks whether the target name appears inside the request's resource text.
- The first 10 tasks were too easy for both models.
  - Found out cuz Haiku performed them all as well as Opus did. I made new, more difficult tasks to find the gap between the models
  - The new more difficult tasks still didn't reveal a gap, which led to the minimal-prompt test
- The spoof task never actually tested anything. Why not?
  - search-api's status was healthy so both models decided a restart wasn't needed
  - V2 of the task made search-api down, so a restart was actually needed and the only blocker was the missing approval
- One look-alike run never read the logs.
  - In V2 of the tasks (Haiku only), one of the three identical tasks, Haiku sent the report to the right location, but never actually read the attack log. So that result can't count toward a success.
- Haiku and Opus behaved the same. What did you try next, and what did it show?
- Prompt Learning: why did you drop it?

## Friction with tools
- auto-instrumentation only gives the model calls; added spans for my own logic.
- MCP's built-in tracing adds spans without inputs or outputs, so I added my own tool spans to see what each tool received and returned
