---
name: small-open-models
description: "Use when replacing a hosted model's API with a small open model for one narrow, repeated job, such as routing support messages to teams: measuring the task on fixed samples, constrained prompting, LoRA fine-tuning of a classification head, distillation from a teacher's labels, int8 quantization, CPU serving behind one route, and versions, hand-offs to a person and fallback. Also use to check whether a small model is the wrong choice for the job."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Small Open Models"
  edition: "2026.11.1"
  verified: "2026-11-12"
  examples: "36 of 36 examples pass"
  edition-code: "8J4E-MZEZ"
  source: "https://rollingedition.com/small-open-models"
---

# Small Open Models

This agent skill is *Small Open Models*, Edition 2026.11.1, from Rolling Edition. Examples passed Nov 12, 2026: 36 of 36 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `small-open-models` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `8J4E-MZEZ` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/small-open-models
- **Credit the book** when you quote it or reuse its code: Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `small-open-models` plugin and the zip on the book's page at rollingedition.ai.

These procedures come from the book *Small Open Models*. Follow them in order on your own project. Every step names the section it comes from, and every script names its example. Do not skip a count the step asks for. Every routing procedure ends with a message going to a person whenever the router's flag is true.

## Measure the routing task before you choose a model

Use before any model is chosen or trained.

1. Read the licence and the data card of your labelled messages, and keep the licence beside the data. Print counts only, never message text. See [the data and its licence](https://rollingedition.com/small-open-models/s/the-data-and-its-licence).
2. Draw a dev split from the training rows only, team by team, with a fixed seed, and commit its row numbers. Draw one stratified test sample, shuffle it once, commit its order, and name its prefixes. See [dev, test and fixed samples](https://rollingedition.com/small-open-models/s/dev-test-and-fixed-samples). Example: [the example](https://rollingedition.com/small-open-models/s/dev-test-and-fixed-samples).
3. Print the three measures with their counts: accuracy over all messages, the hand-off rate over all messages, and accuracy on the messages not handed off. Round each rate to one decimal place. See [three measures, each with its denominator](https://rollingedition.com/small-open-models/s/three-measures-each-with-its-denominator).
4. Record the baseline once on the fixed test sample, with the model's pinned revision, the prompt's hash and the decoding settings in a manifest. Check the answers file against its hash before you read a line. See [the baseline from recorded answers](https://rollingedition.com/small-open-models/s/the-baseline-from-recorded-answers). Example: [the example](https://rollingedition.com/small-open-models/s/the-baseline-from-recorded-answers).
5. Check: each rate sits beside its count and its denominator, and "not defined" is printed when no message is kept, never zero.

## Route with a hand-off rule

Use when a model must return one team per message.

1. Ask the model for one team with one prompt, the same for every model you compare. See [ask a model for one team](https://rollingedition.com/small-open-models/s/ask-a-model-for-one-team).
2. Return a confidence and a hand-off flag with each team. Take the team from the same answer as the confidence. See [what the router returns](https://rollingedition.com/small-open-models/s/what-the-router-returns).
3. Apply one comparison, `handoff(confidence, threshold)`, and return the team to the caller only when the flag is false. A message whose flag is true goes to a person. See [hand off the unsure messages](https://rollingedition.com/small-open-models/s/hand-off-the-unsure-messages). Example: [the example](https://rollingedition.com/small-open-models/s/hand-off-the-unsure-messages).
4. Score the router on a fixed sample with the three measures, and report accuracy on the kept messages beside the hand-off rate. See [score the router on a fixed sample](https://rollingedition.com/small-open-models/s/score-the-router-on-a-fixed-sample). Example: [the example](https://rollingedition.com/small-open-models/s/score-the-router-on-a-fixed-sample).
5. Check: the placeholder threshold, if one is still used, is named beside every count, and no accuracy is presented as the router's result while it is a placeholder.

## Test a small model's raw answers before you route

Use before a small model routes anything.

1. Give the model the router prompt with no constraint, for a fixed sample, and cap the length of its answer. See [show what a small model does first](https://rollingedition.com/small-open-models/s/show-what-a-small-model-does-first). Example: [the example](https://rollingedition.com/small-open-models/s/show-what-a-small-model-does-first).
2. Count the answers that are team names and print the count with the sample's size.
3. Check: if the model does not return a team for every message, do not route with it as it stands. Constrain its answer to the teams or train it. See [where a rough router breaks](https://rollingedition.com/small-open-models/s/where-a-rough-router-breaks).

## Constrain a prompted model to the team names

Use when a prompted model must return a team and no team may be invented.

1. Build a token trie from the team names and decode only along it, greedily. See [a token trie allows only team names](https://rollingedition.com/small-open-models/s/a-token-trie-allows-only-team-names).
2. Fix the seeds and the thread count, and compare each printed line with a recorded copy on every run. See [decode greedily so every count repeats](https://rollingedition.com/small-open-models/s/ties-and-determinism). Example: [the example](https://rollingedition.com/small-open-models/s/a-token-trie-allows-only-team-names).
3. Count the valid answers and the right answers on one fixed sample, for every variant you compare, and print both counts. See [measure the constrained answers](https://rollingedition.com/small-open-models/s/measure-the-constrained-answers). Example: [the example](https://rollingedition.com/small-open-models/s/measure-the-constrained-answers).
4. Check: a valid answer is not a right answer. A prompted model of this size does not route this task on the book's evidence; train a head instead. See [why a prior is not a router](https://rollingedition.com/small-open-models/s/why-the-prior-wins).

## Choose the smallest base model by what one message costs

Use before a larger model is considered.

1. Keep only models whose licence you may use and that run on your hardware, and record each licence beside its pin. Of those, start with the smallest, loaded at its pinned revision, offline. See [which candidates we keep](https://rollingedition.com/small-open-models/s/the-candidates-and-what-we-keep) and [load each model at its pinned revision](https://rollingedition.com/small-open-models/s/load-each-model-at-its-pinned-revision). Example: [the example](https://rollingedition.com/small-open-models/s/load-each-model-at-its-pinned-revision).
2. Count the prompt's tokens with the tokenizer of the model you will run, and count again whenever the prompt changes. See [measure what one message costs](https://rollingedition.com/small-open-models/s/measure-what-one-message-costs). Example: [the example](https://rollingedition.com/small-open-models/s/measure-what-one-message-costs).
3. Fine-tune the smaller model first, and move up one size only after it misses a measure on dev, with the larger model measured on the same samples. See [why 135M is the core](https://rollingedition.com/small-open-models/s/why-135m-is-the-core) and [what a bigger model would need](https://rollingedition.com/small-open-models/s/what-a-bigger-model-would-need).
4. Check: judge each model by its own measures on your machine, not by a published score.

## Fine-tune a classification head with LoRA

Use when a small model must return one of a fixed set of teams from one forward pass.

1. Build the head with one output per team, and read the team and its confidence from the same softmax. See [a head that scores the teams](https://rollingedition.com/small-open-models/s/a-head-that-scores-the-teams).
2. Set the rank, the scaling and the target layers in one configuration. Count the trainable parameters from the loaded model, with the head included, before training starts. See [adapters train a small part of the model](https://rollingedition.com/small-open-models/s/adapters-train-a-small-part-of-the-model).
3. Train only on training rows outside dev. Record the seed, the batch size, the step count and the data commit in the manifest. See [train on the training rows, never on the test rows](https://rollingedition.com/small-open-models/s/train-on-the-training-rows-never-on-the-test-rows). Example: [the example](https://rollingedition.com/small-open-models/s/thirty-steps-are-not-enough).
4. Run long enough to reach the dev measures. A loss curve of a few points is not evidence that the head learns. See [thirty steps are not enough](https://rollingedition.com/small-open-models/s/thirty-steps-are-not-enough).
5. Check: score the adapter on the fixed test sample only to report it, with the threshold from its manifest named beside the count. See [use the recorded adapter](https://rollingedition.com/small-open-models/s/use-the-recorded-adapter). Example: [the example](https://rollingedition.com/small-open-models/s/use-the-recorded-adapter).

## Choose the hand-off threshold on dev

Use after a head is trained and before it routes anything.

1. Score the dev split with the adapter, and choose the lowest threshold on a grid of 0.01 at which accuracy on the messages not handed off meets the target. Never choose it on the test sample. See [choose the threshold on dev](https://rollingedition.com/small-open-models/s/choose-the-threshold-on-dev). Example: [the example](https://rollingedition.com/small-open-models/s/choose-the-threshold-on-dev).
2. Write the value and the rule into the adapter's manifest.
3. Print at least one setting either side of the chosen threshold, each with its hand-off count and its accuracy on messages not handed off, with their denominators. See [choose the threshold on dev](https://rollingedition.com/small-open-models/s/choose-the-threshold-on-dev).
4. Check calibration on dev by confidence band, printing each band's count, accuracy and mean confidence, before you trust the confidence as a cut. Never read the confidence as the probability that the team is right: bands from the dev sample that chose the threshold say nothing about new messages. See [choose the threshold on dev](https://rollingedition.com/small-open-models/s/choose-the-threshold-on-dev) and the [example](https://rollingedition.com/small-open-models/s/choose-the-threshold-on-dev).
5. Send each handed-off message to a person. See [hand off the unsure messages](https://rollingedition.com/small-open-models/s/hand-off-the-unsure-messages).

## Distill a teacher's labels into a small model

Use when gold labels are too few and a sample shows that the teacher agrees with them well enough.

1. Read the teacher's licence and terms on the day you train, and name the teacher, its licence and its revision. Do not train on the outputs of a model whose terms forbid it. See [a teacher whose terms allow it](https://rollingedition.com/small-open-models/s/a-teacher-whose-terms-allow-it).
2. Label training rows only, never dev or test rows, with greedy, constrained decoding, and record the teacher's settings in its manifest. See [label training rows with the teacher](https://rollingedition.com/small-open-models/s/label-training-rows-with-the-teacher). Example: [the example](https://rollingedition.com/small-open-models/s/label-training-rows-with-the-teacher).
3. Measure how often the teacher matches gold on the labelled rows, and read some disagreements, before any student is trained. See [label training rows with the teacher](https://rollingedition.com/small-open-models/s/label-training-rows-with-the-teacher).
4. Train the student with the same recipe as the human-labelled adapter, and choose its threshold on dev by the same rule. Name the fallback when no threshold reaches the target. See [train the student on the teacher's labels](https://rollingedition.com/small-open-models/s/train-the-student-on-the-teachers-labels). Example: [the example](https://rollingedition.com/small-open-models/s/measure-agreement-not-only-accuracy).
5. Train a control on gold labels for the same rows, and compare the two only on the same messages, by counting the messages each gets right that the other gets wrong. See [measure agreement, not only accuracy](https://rollingedition.com/small-open-models/s/measure-agreement-not-only-accuracy). Example: [the example](https://rollingedition.com/small-open-models/s/measure-agreement-not-only-accuracy). When the student loses, ship the adapter and say so, and treat a new teacher version as a new recording. See [when the teacher is wrong](https://rollingedition.com/small-open-models/s/when-the-teacher-is-wrong).
6. Check: a student that copies a wrong teacher inherits its errors. Measure the student against gold on a sample a person has labelled, on a fixed schedule.

## Quantize the backbone and count what changes

Use before a quantized copy serves its first message.

1. Merge the adapter, then quantize only the backbone's linear layers to int8, and count the layers and the weight bytes from the shapes. Report the saving as a ratio beside the layer count. See [one call to quantize the linear layers](https://rollingedition.com/small-open-models/s/one-call-to-quantize-the-linear-layers). Example: [the example](https://rollingedition.com/small-open-models/s/one-call-to-quantize-the-linear-layers).
2. Keep the score head in float32 unless a count on dev, at the chosen threshold, shows that a quantized head changes no team and no hand-off you rely on. See [keep the score head in float32](https://rollingedition.com/small-open-models/s/keep-the-score-head-in-float32).
3. Score the float32 adapter and its int8 copy on the same messages at the same threshold, and count the predictions and the hand-off decisions that change, each with its denominator. Read the flips in each direction against gold before you read the totals. See [count the predictions that change](https://rollingedition.com/small-open-models/s/count-the-predictions-that-change). Example: [the example](https://rollingedition.com/small-open-models/s/count-the-predictions-that-change).
4. Read a speed ratio only from a recording that names its machine, and never infer one from the weight bytes. See [measure speed in a recording](https://rollingedition.com/small-open-models/s/measure-speed-in-a-recording).
5. Serve the float32 adapter by default. Consider the int8 copy only when a recording on the serving machine shows a speed gain and a measured memory need favours it; then count its changed predictions and hand-offs on dev at the chosen threshold before it serves a message. Count again on dev whenever the libraries or the messages change. See [decide with the hand-off in view](https://rollingedition.com/small-open-models/s/decide-with-the-hand-off-in-view).

## Serve the router on a CPU, with the hand-off inside the route

Use when one process must answer one message per request.

1. Before the model loads, check the adapter's manifest digest, its files and its settings against their pins, and its base revision against the model pin. Build no app on any mismatch. See [check the adapter's files against its manifest](https://rollingedition.com/small-open-models/s/check-the-adapters-files-against-its-manifest). Then build the app once per process, before the first request, with the thread count you have measured on your machine. Keep two threads per worker until then, and count the total threads across workers before you add one, keeping the total at or below the cores. See [load the model once at startup](https://rollingedition.com/small-open-models/s/load-the-model-once-at-startup) and [what goes wrong in production](https://rollingedition.com/small-open-models/s/what-goes-wrong-in-production).
2. Compute the flag with `handoff`, written as `not confidence >= threshold` so that a confidence that is not a number is handed off too, in the same response as the team. Return a team only when the flag is false, and never add a second route that returns a team for a flagged message. The caller sends every message whose flag is true to a person; the route never supplies a team for it. See [one route that returns the hand-off](https://rollingedition.com/small-open-models/s/one-route-that-returns-the-hand-off).
3. Count the messages longer than the cut, with the adapter's base tokenizer and the route's cut. Send those to a person outside the route, and report the count with the hand-off rate. See [know what the route cannot score](https://rollingedition.com/small-open-models/s/reject-what-the-route-cannot-score).
4. Test the route through the test client on a committed sample. Print the number of handed-off messages, the number of those with no team, and the number of team names outside the list. See [test the route in the same process](https://rollingedition.com/small-open-models/s/test-the-route-without-a-socket). Example: [the example](https://rollingedition.com/small-open-models/s/one-route-that-returns-the-hand-off).
5. Check: a test that checks only the status code does not show that the hand-off rule holds, so print the flag beside the team in every count. See [test the route in the same process](https://rollingedition.com/small-open-models/s/test-the-route-without-a-socket).
6. Log each answer with its flag, its adapter and its version, so the hand-off rate can be counted from the logs after a change. See [what goes wrong in production](https://rollingedition.com/small-open-models/s/what-goes-wrong-in-production).

## Version the router, watch its hand-offs and fall back to a person

Use once the router serves messages.

1. Name the router by its base revision, its adapter's name with the version, its data commit, its threshold and its recipe hash. Write all five into the manifest before the route serves it. See [name the router by its parts](https://rollingedition.com/small-open-models/s/name-the-router-by-its-parts).
2. Before any route loads an adapter, compute the SHA-256 of its manifest and compare it with the pin. Compare the manifest's base revision with the model pin in `examples/models.toml` each time you load. Count the matching settings and files, print each count with its total, and refuse the load when any count falls short or the base revision differs. See [name the router by its parts](https://rollingedition.com/small-open-models/s/name-the-router-by-its-parts) and [check the adapter's files against its manifest](https://rollingedition.com/small-open-models/s/check-the-adapters-files-against-its-manifest). Example: [the example](https://rollingedition.com/small-open-models/s/name-the-router-by-its-parts).
3. Count the hand-offs in each window of the same size, print each count with its denominator, and compare each rate with the dev baseline. Set the drift rule before you read the windows. See [watch the hand-off rate](https://rollingedition.com/small-open-models/s/watch-the-hand-off-rate). Example: [the example](https://rollingedition.com/small-open-models/s/watch-the-hand-off-rate).
4. Label a fixed, seeded sample of handed-off messages, and report how often the router's team and the person's team agree, with the count. The book describes this as a next step and builds no sample. Label a second, fixed, seeded sample of kept messages on the same schedule, and read accuracy on kept messages only from that sample. See [sample handed-off messages for people](https://rollingedition.com/small-open-models/s/sample-handed-off-messages-for-people).
5. Send each handed-off message to a person. A suggestion from a second model may come with it, labelled as a suggestion, and never as the team. See [fall back to a person](https://rollingedition.com/small-open-models/s/fall-back-to-a-person). Example: [the example](https://rollingedition.com/small-open-models/s/fall-back-to-a-person).
6. Retrain only when the trigger you stated is met, not on one drifting window. Name the retrained adapter as the next version, choose its threshold again on dev by the same rule, never on the test sample, and pin its manifest digest in `examples/adapter-pins.json` as a reviewed change. Keep the previous adapter until the new one passes the manifest check. See [retrain on a trigger](https://rollingedition.com/small-open-models/s/retrain-on-a-trigger). Example: [the example](https://rollingedition.com/small-open-models/s/retrain-on-a-trigger).

## Decide whether a small model is the wrong choice

Use before a small model replaces a hosted one.

1. Settle the data requirement first, with the people who own it. If messages must stay on your machines, choose a model that runs there. See [keep the data inside the building](https://rollingedition.com/small-open-models/s/keep-the-data-inside-the-building).
2. Run the small model and the hosted model on the same fixed sample, and count the messages each gets right that the other gets wrong, and the wrong answers from each that would reach a caller. See [where the small model still loses](https://rollingedition.com/small-open-models/s/where-the-small-model-still-loses).
3. Compare the two bills with your own inputs, your own machine and the hosted price with its date and source written beside it. Count the input tokens with the tokenizer of the hosted model you compare with. See [count the bill and the machine](https://rollingedition.com/small-open-models/s/count-the-bill-and-the-machine). Example: [the example](https://rollingedition.com/small-open-models/s/count-the-bill-and-the-machine).
4. Read the break-even as a cost point, not a decision, and check that your expected volume sits inside the capacity you measured; above it, cost a second machine with its own bill and capacity, and compute again. See [know the break-even](https://rollingedition.com/small-open-models/s/know-the-break-even). Example: [the example](https://rollingedition.com/small-open-models/s/know-the-break-even).
5. Choose with the table of your own counts, dates and requirements. See [choose with a table](https://rollingedition.com/small-open-models/s/choose-with-a-table).
