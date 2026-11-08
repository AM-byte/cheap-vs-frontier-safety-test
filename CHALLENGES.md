# Challenges log

## Experiment challenges
- 

## Friction with tools
- auto-instrumentation only gives the model calls; added spans for my own logic.
- MCP's built-in tracing adds spans without inputs or outputs, so I added my own tool spans to see what each tool received and returned

## Findings
- the finding is what it did in practice, something like: “On long-log tasks, X% of Haiku’s agent runs crossed 100K, which raised its cost per safe task from $A to $B.” And check whether Phoenix’s cost numbers reflect the tier. If they don’t, that’s a second finding.


how does it scale, operational readiness, personas - who's using these products, what key features the look for
different integration points: api, ui

"From experiment to production"

"you didn’t need a “don’t follow instructions in logs” rule, because the approval and scope rules already make obeying an injection a violation. That’s a nice design point for your writeup: good policy rules cover attacks they never mention."

