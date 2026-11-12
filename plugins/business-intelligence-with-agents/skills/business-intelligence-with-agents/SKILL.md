---
name: business-intelligence-with-agents
description: "Use when building, checking or hardening an agent that answers business questions from a data warehouse: text-to-SQL that gets numbers wrong, golden questions and evaluation, layered schema context, a semantic layer with governed metrics (MetricFlow), metrics-first routing, guarded read-only SQL (sqlglot, DuckDB), declining unanswerable or stale questions with provenance, row filters, masking and small-group suppression by role, judging answers and gating changes in CI, and serving metrics as MCP tools."
license: CC-BY-4.0
compatibility: "Python 3.12.15 and the pinned packages in scripts/requirements.txt; the scripts run offline."
metadata:
  publisher: "Rolling Edition"
  book: "Business Intelligence with Agents"
  edition: "2026.11.8"
  verified: "2026-11-12"
  examples: "78 of 78 examples pass"
  edition-code: "4VTV-2H9T"
  source: "https://rollingedition.com/business-intelligence-with-agents"
---

# Business Intelligence with Agents

This agent skill is *Business Intelligence with Agents*, Edition 2026.11.8, from Rolling Edition. Examples passed Nov 12, 2026: 78 of 78 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, `references/` holds each chapter, and `scripts/` holds the examples as the edition ran them.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section in `references/` before you act on it, and adapt it to the project in front of you.
- **Check against the book.** Each example in `scripts/` has its expected output beside it (`.out`), at the versions in `scripts/requirements.txt`. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `4VTV-2H9T` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/business-intelligence-with-agents
- **Credit the book** when you quote it or reuse its code: Business Intelligence with Agents, Edition 2026.11.8, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

To run an example as the book does, with [uv](https://docs.astral.sh/uv/):

```sh
uv venv --python 3.12.15
uv pip install -r scripts/requirements.txt
cd scripts && ../.venv/bin/python load-the-warehouse.py
```

## Score an agent's answers on golden questions by outcome

**When:** An agent answers business questions from a warehouse, and someone asks how often its numbers are right. Use this before reporting a change as an improvement.

1. Take each question with its golden result and kind, including questions that should be declined ([Score both on five golden questions](references/bi-agent-end-to-end.md#score-five-questions)).
2. Sort each reply as correct, wrong, error or declined. A result is correct when it has as many rows as the golden result and every golden column's values, within 0.05 percent or half a cent, in any row order unless the question sets one. A decline is correct on a question that should be declined, and any result there is wrong ([Score both on five golden questions](references/bi-agent-end-to-end.md#score-five-questions)).
3. Report the four counts separately. A decline is not a wrong number ([Score both on five golden questions](references/bi-agent-end-to-end.md#score-five-questions)).
4. Read each decline's trace. Check that its reason is about what the agent was given ([Read the trace of one run](references/bi-agent-end-to-end.md#read-one-trace)).
5. Score a metric-based agent and a schema-only SQL agent on the same questions, with the same rule ([Score both on five golden questions](references/bi-agent-end-to-end.md#score-five-questions)).

**Check:** Run [the example](scripts/score-five-golden.py) and compare its `metric correct: …` line, 4 of 5, with your own run.

**Pitfalls:**
- A plausible wrong number reaches a decision unless each answer is scored against a golden result ([What goes wrong in production](references/bi-agent-end-to-end.md#end-to-end-in-production)).
- A decline with a false reason stops people asking elsewhere ([What goes wrong in production](references/bi-agent-end-to-end.md#end-to-end-in-production)).

## Count the plausible wrong numbers by kind

**When:** An agent writes SQL over a warehouse you don't own, and its wrong answers run without errors.

1. Check the grain of each summed column in every join, and compare row counts with distinct keys ([Joins that fan out and inflate a sum](references/wrong-numbers.md#joins-that-fan-out)).
2. Look up each business word, such as "revenue", as a definition with its owner. If none is written, the agent asks or declines ([Definitions the schema doesn't hold](references/wrong-numbers.md#definitions-not-in-schema)).
3. Check period questions at boundaries where UTC and local days, or calendar and fiscal years, disagree ([Time zones and the fiscal calendar](references/wrong-numbers.md#time-and-calendars)).
4. Check each table the query reads against the allowed list, which leaves out legacy tables ([The table with the tempting name](references/wrong-numbers.md#the-tempting-table)).
5. Move each rule about which rows count into the marts where you can. Where a mart keeps the rows, as with cancelled orders, write the rule into the definition the agent uses, and add a golden question that fails when the rule is left out ([Filters nobody wrote down](references/wrong-numbers.md#unwritten-filters)).
6. Grade each answer against its golden result, and count the wrong numbers by kind ([Count the failures by kind](references/wrong-numbers.md#count-failures-by-kind)).

**Check:** Run [the example](scripts/classify-schema-only-errors.py) and compare its `wrong answers with time: …` line, 6, with your own run.

**Pitfalls:**
- Two errors can cancel out and look right, so compare every result with its golden result ([What goes wrong in production](references/wrong-numbers.md#wrong-numbers-in-production)).
- A legacy table can reappear after a schema change, so log the tables each answer reads ([What goes wrong in production](references/wrong-numbers.md#wrong-numbers-in-production)).

## Build golden questions from the work people do

**When:** You need to measure an agent on a warehouse, and no golden questions exist yet.

1. Collect real requests from the team's queue, keeping each asker's wording ([Write questions from the work people do](references/golden-questions.md#write-golden-questions)).
2. Give each question a role, a kind and a note naming the definition its gold follows. A note needing more than one sentence means a decline ([Write questions from the work people do](references/golden-questions.md#write-golden-questions)).
3. Check each gold before it scores: it must run, return rows without NULLs, and, where you can, agree with an independent check query ([Check the gold before you trust it](references/golden-questions.md#check-the-gold)).
4. Compare answers with one function that ignores row order and column names, unless the question ranks ([Order, rounding and column names](references/golden-questions.md#order-rounding-names)).
5. Include ambiguous and unanswerable declines and forbidden questions, tag each question with the traps it tests, and count kinds, roles and traps per split before scoring ([Cover declines and roles, not only answers](references/golden-questions.md#cover-declines-and-roles)).
6. Split into dev and test before tuning, and report both scores ([Hold out a test split](references/golden-questions.md#hold-out-a-test-split)).

**Check:** Run [the example](scripts/golden-coverage.py) and compare its `traps missing from a split: …` line, none, with your count.

**Pitfalls:**
- The gold goes stale silently when a definition changes. Re-run the check queries on each change ([What goes wrong in production](references/golden-questions.md#golden-questions-in-production)).
- The test split leaks when people tune to its questions, so keep it out of tuning talk ([What goes wrong in production](references/golden-questions.md#golden-questions-in-production)).

## Add context layers and measure each one

**When:** An agent writes SQL on someone else's warehouse and gets numbers wrong because the schema leaves a meaning open.

1. List each reading of the schema that answers one real question, and keep the whole schema while it fits. ([What the schema says, and what it doesn't](references/layered-context.md#what-the-schema-says))
2. Write column notes only where a name misleads. ([Describe columns where names mislead](references/layered-context.md#describe-columns))
3. Write a glossary entry for each business word whose meaning was chosen. ([Add the business glossary](references/layered-context.md#add-the-glossary))
4. Retrieve a few verified queries per question by similarity, set a minimum score and check it on questions the warehouse can't answer, and never let a golden question into the verified set. ([Retrieve verified queries as examples](references/layered-context.md#retrieve-verified-queries))
5. Set a token budget well inside the model's window, fit each question's context to it by a priority you have measured, and never drop the schema when it fits. ([Fit the context to a budget](references/layered-context.md#fit-a-context-budget))
6. Measure one layer at a time on dev, then check the chosen set once on test. ([Measure what each layer adds](references/layered-context.md#measure-each-layer)), ([Check the chosen layers on test](references/layered-context.md#check-layers-on-test))

**Check:** run [the example](scripts/layer-ablation-dev.py) and compare its line `schema+columns correct: …`, written as 9.

**Pitfalls:**
- Notes drift from the marts silently, so check in CI that each named column exists. ([What goes wrong in production](references/layered-context.md#layered-context-in-production))
- A rule stated in context is still ignored, so score every change per question. ([What goes wrong in production](references/layered-context.md#layered-context-in-production))

## Define metrics once and check them against the data

**When:** Several tables feed the same business numbers, and their definitions disagree.

1. Describe each table as one semantic model, and count duplicates of each primary entity in the data. ([Describe each table as a semantic model](references/semantic-layer.md#entities-measures-dimensions))
2. Join only many rows to one, and define a metric on a finer table rather than joining to it. ([Join through entities so sums can't fan out](references/semantic-layer.md#join-through-entities))
3. Write each rate as a ratio of two simple metrics, each with its own filter and time dimension. ([Build ratio and derived metrics from simple ones](references/semantic-layer.md#ratio-and-derived-metrics))
4. Put fiscal periods in the time spine as custom grains. ([Put the fiscal calendar in the time spine](references/semantic-layer.md#time-grains-and-fiscal))
5. Accept requests made of names and values, never SQL. ([Compile a metric request to SQL](references/semantic-layer.md#compile-a-metric-request))
6. Compare the layer with MetricFlow 0.213.0 on each request shape you rely on. ([Check the definitions against MetricFlow](references/semantic-layer.md#check-against-metricflow))

**Check:** run [the example](scripts/load-semantic-models.py) and compare its line `problems in the shop's definitions: …`, written as 0.

**Pitfalls:**
- A foreign key declared primary turns off the fan-out protection, and sums inflate without an error. ([What goes wrong in production](references/semantic-layer.md#semantic-layer-in-production))
- Never pass a filter string written by a model or a user to the layer, because filters are templates. ([What goes wrong in production](references/semantic-layer.md#semantic-layer-in-production))

## Route questions to governed metrics and validate requests

**When:** An agent answers business questions from a semantic layer, and its wrong answers are valid requests for the wrong metric, filter or period.

1. Give the agent the layer's metrics and their dimensions, and keep tables out of its tools. ([Give the agent metrics, not tables](references/metrics-first.md#metrics-not-tables))
2. Have the model return the request as structured tool arguments, and parse it into a typed request before anything runs. ([Ask for a request, not SQL](references/metrics-first.md#request-not-sql))
3. Validate names, categorical values and date grains before compiling, and return each refusal with the allowed alternatives. ([Validate the request against the layer](references/metrics-first.md#validate-the-request))
4. Ask back only when every option leads to a request the layer can serve; when none does, decline. ([Ask back when a question is ambiguous](references/metrics-first.md#ask-back-when-ambiguous))
5. Score on golden questions, tuning on dev only. ([Measure metrics-first on the golden questions](references/metrics-first.md#measure-metrics-first))

**Check:** run [the example](scripts/reject-unknown-dimension.py) and compare its line `matches golden: …`, written as True.

**Pitfalls:**
- Two metrics fit the same words, and the agent picks the other one. Keep one metric per business term. ([What goes wrong in production](references/metrics-first.md#metrics-first-in-production))
- Asking back becomes the answer to everything. Count clarifications as a cost. ([What goes wrong in production](references/metrics-first.md#metrics-first-in-production))

## Run the agent's SQL through guards

**When:** An agent writes SQL on someone else's warehouse for a question no metric covers.

1. Connect read-only to a database holding only the tables the agent may read, with file access off ([Give the agent a database with only what it may read](references/guarded-sql.md#least-privilege-database)).
2. Parse the SQL into a tree and accept exactly one statement. Check nodes, not text ([Parse the SQL before it runs](references/guarded-sql.md#parse-before-running)).
3. Accept only a query at the root, walk every node for writes, and allow only listed tables ([Allow only read-only queries on known tables](references/guarded-sql.md#read-only-allowlist)).
4. Add a row limit that keeps any smaller one the agent wrote, refuse a result over a size limit, and refuse a plan whose `EXPLAIN` estimate is over a limit set from your known-good queries, or that has a step with no estimate ([Bound the rows and the cost](references/guarded-sql.md#bound-rows-and-cost)).
5. Run the query in a worker process that a deadline kills ([Enforce the deadline by killing a process](references/guarded-sql.md#time-the-plan)).
6. Repair at most once, from the guard's refusal or the warehouse's error ([Repair once from the error](references/guarded-sql.md#repair-once)).

**Check:** run [the example](scripts/block-a-delete.py) and compare its line `statements in the tree: …`, written as Select, Delete.

**Pitfalls:**
- A wrong answer passes every guard. Read empty or `NULL` results ([What goes wrong in production](references/guarded-sql.md#guarded-sql-in-production)).
- A read-only database keeps state. Give each query a fresh cursor ([What goes wrong in production](references/guarded-sql.md#guarded-sql-in-production)).
- Repair hides errors. Count repaired answers in every score ([What goes wrong in production](references/guarded-sql.md#guarded-sql-in-production)).

## Decline the questions the warehouse can't answer

**When:** An agent answers questions on someone else's warehouse that may have several readings, no answer, or a period not yet loaded.

1. Sort each question with no single answer into ambiguous or unanswerable, and note any nearby column a model could mistake for the answer ([Kinds of questions the warehouse can't answer](references/say-when-it-cannot.md#kinds-of-unanswerable)).
2. Ask back on an ambiguous question only when every reading is answerable. Otherwise decline ([Kinds of questions the warehouse can't answer](references/say-when-it-cannot.md#kinds-of-unanswerable)).
3. Make declining a run-ending tool with a fixed kind and a sentence naming what is missing ([Decline with a reason](references/say-when-it-cannot.md#decline-with-a-reason)).
4. Before each answer that names a period, compare each feed's newest load with the period's end plus the metric's settling window. Decline as stale when a feed stops short ([Check freshness before answering](references/say-when-it-cannot.md#check-freshness)).
5. Show each answer with its metric name and definition first, then its filters, period, role and data as of; show each decline with its kind, reason and role ([Show the provenance with every answer](references/say-when-it-cannot.md#show-provenance)).

**Check:** run [the example](scripts/cannot-answer-tool.py) and compare its line `gq-019 ended with: …`, written as cannot_answer, kind no_definition.

**Pitfalls:**
- A quiet feed looks stale. Count stale declines per feed ([What goes wrong in production](references/say-when-it-cannot.md#declining-in-production)).
- A confidence target isn't calibration. Prefer checks in code ([What goes wrong in production](references/say-when-it-cannot.md#declining-in-production)).
- A question back can settle half the question. Name metrics in the options ([What goes wrong in production](references/say-when-it-cannot.md#declining-in-production)).

## Enforce each role's access below the agent

**When:** An agent on someone else's project answers for several roles over shared tables, and each role's rows, columns or group sizes are limited.

1. Take the role from sign-in, never from a question, and keep rules out of the prompt ([A rule in the prompt is not a control](references/who-may-see-what.md#prompt-rules-fail)).
2. Write a row filter for every table a role can reach, and refuse the rest ([Apply row filters in the compiler](references/who-may-see-what.md#row-filters-in-compiler)).
3. Replace each table a query reads with a filtered subquery, so later joins see only those rows ([Apply row filters in the compiler](references/who-may-see-what.md#row-filters-in-compiler)).
4. Mask a column by replacing its table, so a `WHERE` or join sees the mask too ([Mask columns in every path](references/who-may-see-what.md#mask-every-path)).
5. Suppress groups below a minimum number of distinct customers ([Suppress groups small enough to identify someone](references/who-may-see-what.md#suppress-small-groups)).
6. Write one audit entry per question, from code ([Log who asked what, and what ran](references/who-may-see-what.md#log-who-asked)).

**Check:** run [the example](scripts/masked-emails.py) and compare its line `the largest group by email, finance: 3040`.

**Pitfalls:**
- A role taken from a request's arguments lets the asker claim any role ([What goes wrong in production](references/who-may-see-what.md#access-in-production)).
- A table with no rule must not stay open. Test the policy file in CI against every table ([What goes wrong in production](references/who-may-see-what.md#access-in-production)).
- Suppression protects one answer, not a person across answers ([Subtracting two answers recovers a group](references/who-may-see-what.md#differencing-limit)).

## Gate a change on paired repeated runs

**When:** A change to an agent's prompt, context or metrics needs a merge decision, and the project has golden questions and recorded runs.

1. Score the base and the candidate on the same questions: correct with a Wilson interval, wrong numbers, declines and failures ([Score a run on more than accuracy](references/catch-regressions.md#score-a-run)).
2. Record the base and the candidate with several seeds per question, at the sampling settings you serve, and confirm once that a seed replays exactly ([Repeat runs to see the variance](references/catch-regressions.md#repeat-to-see-variance)).
3. For each question, take the share of runs correct under each configuration, and their difference ([Gate a change in CI](references/catch-regressions.md#gate-a-change)).
4. Fail on any stable break (a question the base got right in at least four of five runs and the candidate in at most one), and on a mean paired difference whose t interval lies below zero. Write both rules down as your choice ([Gate a change in CI](references/catch-regressions.md#gate-a-change)).
5. Compute the smallest change these rules detect on your set, and read the questions that moved before you change a rule ([Gate a change in CI](references/catch-regressions.md#gate-a-change)).

**Check:** run [the example](scripts/regression-gate.py) and compare its line `gate: fail`.

**Pitfalls:**
- A gate that fails on noise gets switched off. Set its rules with the people who answer for the numbers ([What goes wrong in production](references/catch-regressions.md#regressions-in-production)).
- Recording the dev split again and again while tuning makes it optimistic. Count each split's recordings in its manifest ([What goes wrong in production](references/catch-regressions.md#regressions-in-production)).
- A lower temperature hides variance rather than removing it ([What goes wrong in production](references/catch-regressions.md#regressions-in-production)).

## Serve governed metrics over MCP with the role bound

**When:** Metrics with per-person access rules are to be served to an assistant over MCP.

1. Register the tools your agent was measured with, each a thin call into the same code, in a fixed order ([Turn metrics into tools](references/serve-over-mcp.md#metrics-as-tools)).
2. Bind the role at sign-in: from the environment for stdio, or from a verified token on each HTTP request ([Carry the caller's role into every query](references/serve-over-mcp.md#carry-the-role)).
3. Leave `role` out of every input schema ([Carry the caller's role into every query](references/serve-over-mcp.md#carry-the-role)).
4. Open the role's own read-only database when the server binds the role ([Carry the caller's role into every query](references/serve-over-mcp.md#carry-the-role)).
5. Return answers as structured content with provenance. Raise a tool error, saying how to fix it, for a request the model can correct, and return an access refusal as an answer that declines ([Return answers with their provenance](references/serve-over-mcp.md#return-provenance)).
6. Test each role's server in memory, including a check that fails on a wrong binding ([Test the server in memory](references/serve-over-mcp.md#test-the-server)).

**Check:** run [the example](scripts/role-bound-at-build.py) and compare its line `role bound at build, countries: DE, ES, FR, GB, NL`.

**Pitfalls:**
- One stdio server shared by several people gives everyone the role of whoever started it ([What goes wrong in production](references/serve-over-mcp.md#serving-in-production)).
- An unknown role claim must fail closed, not fall back to a default ([What goes wrong in production](references/serve-over-mcp.md#serving-in-production)).
- A server that binds one role but queries with another's connection is one bug away from a leak ([What goes wrong in production](references/serve-over-mcp.md#serving-in-production)).
