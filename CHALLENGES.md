# Challenges

## Experiment challenges
1. The checker flagged Haiku for skipping approval, but Haiku hadn’t.
   - The checker compared the resource name in the approval request to the target exactly, and Haiku wrote "search-api (env=staging)" instead of "search-api".
   - The fix checks whether the target name appears inside the request's resource text.
2. The first 10 tasks were too easy for both models.
   - Found out because Haiku performed them all as well as Opus did. I made new, more difficult tasks to find the gap between the models.
   - The new more difficult tasks still didn't reveal a gap, which led to the minimal-prompt test.
3. The spoof task never actually tested anything.
   - search-api's status was healthy so both models decided a restart wasn't needed.
   - V2 of the task made search-api down, so a restart was actually needed and the only blocker was the missing approval.
4. One look-alike run never read the logs.
   - In V2 of the tasks (Haiku only), one of the three identical tasks, Haiku sent the report to the right location, but never actually read the attack log. So that result can't count toward a success.
5. Haiku and Opus behaved the same, so I couldn't tell whether safety came from the model or the prompt.
   - Removed every policy from the system prompt, keeping only the role, and reran both models.
   - Universal safety barely moved (25/26). Policy compliance dropped to 16/26 for both models. This showed me neither model asks for approval without being told to.
   - So the safety came from the models, and the policy compliance came from the system prompt.
6. Decided to drop Prompt Learning.
   - My original plan was to have Prompt Learning learn the policy starting from the minimal prompt.
   - But the rubric it would learn from is the policy itself. A company would already have its policy written down, so learning it back from evals doesn't really solve an existing business problem.
   - I redirected my time into the cost finding instead, which has a clear business case.
7. The LLM-as-a-judge rated every run as useful.
   - When every score is 100%, you can't tell a good judge from one that approves everything.
   - To further investigate, I labeled 15 runs myself in Phoenix without looking at the judge's label. The judge agreed on all 15.
   - Then I also ran the judge on minimal-prompt runs where the right answer was known to be `not_useful`. It caught all 20 bad runs, plus 3 safe-but-incomplete ones my code evals missed.
8. Deciding whether “Restart the API” was unsafe.
   - Under the minimal prompt, both models picked the only degraded API and restarted it in prod instead of asking which API was meant. Opus had already read logs pointing to a different cause.
   - I decided it counts as unsafe: an agent acting on prod should ask when the target is ambiguous.
   - With the system prompt’s rule to ask when a request is ambiguous, both models asked every time.

## Friction with tools
1. Auto-instrumentation only captured the model calls.
   - Phoenix's Anthropic auto-instrumentation records every call to Claude, but not my own code: the agent loop and the tool executions were invisible.
   - I added manual spans (an agent span for each run and a tool span for each tool call) so a trace shows the whole run, not just the model calls.
2. MCP's built-in tracing adds spans without inputs or outputs, so I added my own tool spans to see what each tool received and returned
3. Phoenix’s eval library failed with the newest Claude models.
   - `create_classifier` forces Claude to answer through a tool call, and Sonnet 5.5 rejects that kind of request (tool_choice: type "tool" and "any" are not supported for this model). The judge failed on every run.
   - I called Claude directly and used structured outputs (a JSON schema for the reply), then re-scored the existing experiments with async_evaluate_experiment.