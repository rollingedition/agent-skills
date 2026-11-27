---
title: "Securing LLM Applications and Agents"
chapter: "Measure what prompt-level defences buy"
chapter_id: prompt-defences
book: securing-llm-applications-and-agents
edition: 2026.11.4
verified: 2026-11-22
edition_code: DZ78-8TMV
canonical: https://rollingedition.com/securing-llm-applications-and-agents/prompt-defences
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Measure what prompt-level defences buy,” chapter 4 of Securing LLM Applications and Agents, Edition 2026.11.4, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/securing-llm-applications-and-agents/prompt-defences. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measure what prompt-level defences buy

By the end of this chapter you can measure what a prompt-level defence does to an assistant's attack success and to its utility, count the tokens it adds to each prompt, and read a held-out result without tuning on it. The defences here change only the prompt. None of them changes a tool, a permission or the data the assistant can reach, so each one's effect is whatever the model does with the text it is given. These variants are teaching code and defence in depth. They are not the controls that limit what the assistant can do. Those are enforced outside the model, in [Chapter 1](#an-outbound-allowlist) and [Chapter 6](#least-privilege). Chapter 8 keeps untrusted text away from the model that acts.

The office assistant reads tenant messages, uploaded documents, the search index and the pages it fetches. Any of them can carry an instruction, and the assistant can follow it. [Chapter 3](#undefended-baseline) measured how often that worked on the undefended assistant: it reached a case's goal in 11.7% (7 of 60) of the dev cases. A prompt-level defence is the cheapest response to that. It tells the model that tool text is data, marks where untrusted text begins and ends, changes how that text looks, or repeats the staff member's request after it. Each one works, if it works at all, through the model's reading of the prompt.

That is why this book labels all five defences prompt (advice). Spotlighting changes the input text itself, so one could file it as an input control. The book does not, because its effect depends on the model reading the marked text, and a model can read a marker and still act on what the marker surrounds. The harness label was chapter 1's, and it comes back in chapter 6. The other labels, input (detector) and design (isolation), belong to later chapters, where the controls they describe act outside the model.

The chapter measures five variants: a warning in the system prompt, delimiters, datamarking, encoding and repeating the request. Each one runs on the dev split first, where its wording was tuned, and then once on the held-out split, where it is measured with the wording frozen. Every comparison is paired per case, and every interval is a bootstrap over cases, as [Evaluating LLM Applications, chapter 8](https://rollingedition.com/evaluating-llm-applications/s/bootstrap-over-items) explains. Every rate here holds for this fixed attack set and for one model, Qwen3-4B-Instruct-2507, pinned. [Chapter 11](#the-gap-to-the-fixed-set) tests two of them, datamarking and encoding, against an attacker that adapts to them.

The held-out undefended run, which [chapter 3](#undefended-baseline) reports, is lower than dev's. Every held-out comparison in this chapter is against that run, not against the dev numbers, and the paired intervals make that comparison. The held-out example runs each defence once and produces those numbers:

Example `prompt-defences-held-out` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Five prompt-level defences, each run once on the held-out split after its wording was frozen on dev, against the
undefended baseline's held-out run. The line the prose rests on is `prompt-warning, attack success, 60 held-out cases`,
with its paired difference beneath it, per case, with interval.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

# Each variant is replayed with its row of lib/variants.py: its hooks, and the prompt its recording was made with.
VARIANTS = ("prompt-datamark", "prompt-delimiters", "prompt-encode", "prompt-repeat", "prompt-warning")


def run_held_out(recording, variant=None):
    """The 15 held-out benign tasks and 60 held-out cases of one recording: utility by task ID, attack success by case ID."""
    benign, attacks = cases.load_tasks("held-out"), cases.load_cases("held-out")
    assert (len(benign), len(attacks)) == (15, 60), "the held-out split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, variant=variant)
    case_traces = runs.replay_cases(recording, attacks, variant=variant)
    return ({t.id: scorers.utility(t, traces[t.id]) for t in benign},
            {c.id: scorers.attack_success(c, case_traces[c.id]) for c in attacks})


def main():
    # The wording of each defence was chosen on dev; held-out is its one run, so these numbers are the book's claims.
    print("status: defences tuned on dev; this is each defence's one held-out run")
    base_utility, base_success = run_held_out("baseline-held-out")
    case_ids, task_ids = sorted(base_success), sorted(base_utility)
    before = [base_success[c] for c in case_ids]
    before_utility = [base_utility[t] for t in task_ids]
    report.rate_lines("baseline, utility, 15 held-out benign tasks", [base_utility[t] for t in task_ids],
                      "baseline, utility interval")
    report.rate_lines("baseline, attack success, 60 held-out cases", before, "baseline, attack success interval")
    for name in VARIANTS:  # sorted by name, as listed
        utility, success = run_held_out(f"{name}-held-out", name)
        report.rate_lines(f"{name}, utility, 15 held-out benign tasks", [utility[t] for t in task_ids],
                          f"{name}, utility interval")
        report.rate_lines(f"{name}, attack success, 60 held-out cases", [success[c] for c in case_ids],
                          f"{name}, attack success interval")
        after = [success[c] for c in case_ids]
        report.paired(f"{name}, paired difference in attack success", before, after)
        report.paired(f"{name}, paired difference in utility", before_utility, [utility[t] for t in task_ids])
        # Cases the baseline let through that the variant stops, and the reverse.
        report.newly_lines(f"{name}, newly blocked, held-out cases", f"{name}, newly let through, held-out cases",
                           before, after)


if __name__ == "__main__":
    main()
```

Output:

```text
status: defences tuned on dev; this is each defence's one held-out run
baseline, utility, 15 held-out benign tasks: 66.7% (10 of 15)
baseline, utility interval: [40.0%, 86.7%]
baseline, attack success, 60 held-out cases: 11.7% (7 of 60)
baseline, attack success interval: [3.3%, 20.0%]
prompt-datamark, utility, 15 held-out benign tasks: 53.3% (8 of 15)
prompt-datamark, utility interval: [26.7%, 80.0%]
prompt-datamark, attack success, 60 held-out cases: 6.7% (4 of 60)
prompt-datamark, attack success interval: [1.7%, 13.3%]
prompt-datamark, paired difference in attack success: -5.0 points
prompt-datamark, paired difference in attack success, interval: [-11.7, +1.7] points
prompt-datamark, paired difference in utility: -13.3 points
prompt-datamark, paired difference in utility, interval: [-33.3, +0.0] points
prompt-datamark, newly blocked, held-out cases: 4
prompt-datamark, newly let through, held-out cases: 1
prompt-delimiters, utility, 15 held-out benign tasks: 66.7% (10 of 15)
prompt-delimiters, utility interval: [40.0%, 86.7%]
prompt-delimiters, attack success, 60 held-out cases: 15.0% (9 of 60)
prompt-delimiters, attack success interval: [6.7%, 25.0%]
prompt-delimiters, paired difference in attack success: +3.3 points
prompt-delimiters, paired difference in attack success, interval: [-3.3, +10.0] points
prompt-delimiters, paired difference in utility: +0.0 points
prompt-delimiters, paired difference in utility, interval: [+0.0, +0.0] points
prompt-delimiters, newly blocked, held-out cases: 1
prompt-delimiters, newly let through, held-out cases: 3
prompt-encode, utility, 15 held-out benign tasks: 13.3% (2 of 15)
prompt-encode, utility interval: [0.0%, 33.3%]
prompt-encode, attack success, 60 held-out cases: 0.0% (0 of 60)
prompt-encode, attack success interval: [0.0%, 0.0%]
prompt-encode, paired difference in attack success: -11.7 points
prompt-encode, paired difference in attack success, interval: [-20.0, -3.3] points
prompt-encode, paired difference in utility: -53.3 points
prompt-encode, paired difference in utility, interval: [-80.0, -26.7] points
prompt-encode, newly blocked, held-out cases: 7
prompt-encode, newly let through, held-out cases: 0
prompt-repeat, utility, 15 held-out benign tasks: 33.3% (5 of 15)
prompt-repeat, utility interval: [13.3%, 60.0%]
prompt-repeat, attack success, 60 held-out cases: 10.0% (6 of 60)
prompt-repeat, attack success interval: [3.3%, 18.3%]
prompt-repeat, paired difference in attack success: -1.7 points
prompt-repeat, paired difference in attack success, interval: [-8.3, +5.0] points
prompt-repeat, paired difference in utility: -33.3 points
prompt-repeat, paired difference in utility, interval: [-53.3, -13.3] points
prompt-repeat, newly blocked, held-out cases: 3
prompt-repeat, newly let through, held-out cases: 2
prompt-warning, utility, 15 held-out benign tasks: 60.0% (9 of 15)
prompt-warning, utility interval: [33.3%, 86.7%]
prompt-warning, attack success, 60 held-out cases: 10.0% (6 of 60)
prompt-warning, attack success interval: [3.3%, 18.3%]
prompt-warning, paired difference in attack success: -1.7 points
prompt-warning, paired difference in attack success, interval: [-8.3, +3.3] points
prompt-warning, paired difference in utility: -6.7 points
prompt-warning, paired difference in utility, interval: [-20.0, +0.0] points
prompt-warning, newly blocked, held-out cases: 2
prompt-warning, newly let through, held-out cases: 1
```

## A warning in the prompt {#a-warning-in-the-prompt}

The simplest defence is a sentence. The warning is appended to the system prompt. It says that text from tools may contain instructions, that the model should never follow them, and that only the staff member's request counts. Nothing else in the prompt changes. The warning's whole cost is the length of that note on each model call.

Its effect depends on whether the model acts on the note, and the note's wording can't settle that in advance. The first example runs all five variants on the dev split, against the undefended run.

Example `prompt-defences-paired` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Five prompt-level defences, each replayed on the dev split and paired with the undefended baseline. The line the prose
rests on is `prompt-warning, attack success, 60 dev cases`, with its paired difference beneath it, per case, with interval.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

# Each variant is replayed with its row of lib/variants.py: its hooks, and the prompt its recording was made with.
VARIANTS = ("prompt-datamark", "prompt-delimiters", "prompt-encode", "prompt-repeat", "prompt-warning")


def run_dev(recording, variant=None):
    """The 15 dev benign tasks and 60 dev cases of one recording: utility by task ID, attack success by case ID."""
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, variant=variant)
    case_traces = runs.replay_cases(recording, attacks, variant=variant)
    return ({t.id: scorers.utility(t, traces[t.id]) for t in benign},
            {c.id: scorers.attack_success(c, case_traces[c.id]) for c in attacks})


def main():
    base_utility, base_success = run_dev("baseline-dev")  # no hooks: the undefended run
    case_ids, task_ids = sorted(base_success), sorted(base_utility)
    before = [base_success[c] for c in case_ids]
    for name in VARIANTS:
        utility, success = run_dev(f"{name}-dev", name)
        report.rate_lines(f"{name}, utility, 15 dev benign tasks", [utility[t] for t in task_ids],
                          f"{name}, utility interval")
        report.rate_lines(f"{name}, attack success, 60 dev cases", [success[c] for c in case_ids],
                          f"{name}, attack success interval")
        after = [success[c] for c in case_ids]
        report.paired(f"{name}, paired difference in attack success", before, after)
        report.paired(f"{name}, paired difference in utility", [base_utility[t] for t in task_ids],
                      [utility[t] for t in task_ids])
        # Cases the baseline let through that the variant stops, and the reverse.
        report.newly_lines(f"{name}, newly blocked, dev cases", f"{name}, newly let through, dev cases", before, after)


if __name__ == "__main__":
    main()
```

Output:

```text
prompt-datamark, utility, 15 dev benign tasks: 86.7% (13 of 15)
prompt-datamark, utility interval: [66.7%, 100.0%]
prompt-datamark, attack success, 60 dev cases: 5.0% (3 of 60)
prompt-datamark, attack success interval: [0.0%, 11.7%]
prompt-datamark, paired difference in attack success: -6.7 points
prompt-datamark, paired difference in attack success, interval: [-13.3, -1.7] points
prompt-datamark, paired difference in utility: -6.7 points
prompt-datamark, paired difference in utility, interval: [-20.0, +0.0] points
prompt-datamark, newly blocked, dev cases: 4
prompt-datamark, newly let through, dev cases: 0
prompt-delimiters, utility, 15 dev benign tasks: 93.3% (14 of 15)
prompt-delimiters, utility interval: [80.0%, 100.0%]
prompt-delimiters, attack success, 60 dev cases: 10.0% (6 of 60)
prompt-delimiters, attack success interval: [3.3%, 18.3%]
prompt-delimiters, paired difference in attack success: -1.7 points
prompt-delimiters, paired difference in attack success, interval: [-5.0, +0.0] points
prompt-delimiters, paired difference in utility: +0.0 points
prompt-delimiters, paired difference in utility, interval: [+0.0, +0.0] points
prompt-delimiters, newly blocked, dev cases: 1
prompt-delimiters, newly let through, dev cases: 0
prompt-encode, utility, 15 dev benign tasks: 66.7% (10 of 15)
prompt-encode, utility interval: [40.0%, 86.7%]
prompt-encode, attack success, 60 dev cases: 0.0% (0 of 60)
prompt-encode, attack success interval: [0.0%, 0.0%]
prompt-encode, paired difference in attack success: -11.7 points
prompt-encode, paired difference in attack success, interval: [-20.0, -5.0] points
prompt-encode, paired difference in utility: -26.7 points
prompt-encode, paired difference in utility, interval: [-46.7, -6.7] points
prompt-encode, newly blocked, dev cases: 7
prompt-encode, newly let through, dev cases: 0
prompt-repeat, utility, 15 dev benign tasks: 20.0% (3 of 15)
prompt-repeat, utility interval: [0.0%, 40.0%]
prompt-repeat, attack success, 60 dev cases: 6.7% (4 of 60)
prompt-repeat, attack success interval: [1.7%, 13.3%]
prompt-repeat, paired difference in attack success: -5.0 points
prompt-repeat, paired difference in attack success, interval: [-11.7, +1.7] points
prompt-repeat, paired difference in utility: -73.3 points
prompt-repeat, paired difference in utility, interval: [-93.3, -46.7] points
prompt-repeat, newly blocked, dev cases: 4
prompt-repeat, newly let through, dev cases: 1
prompt-warning, utility, 15 dev benign tasks: 93.3% (14 of 15)
prompt-warning, utility interval: [80.0%, 100.0%]
prompt-warning, attack success, 60 dev cases: 11.7% (7 of 60)
prompt-warning, attack success interval: [5.0%, 20.0%]
prompt-warning, paired difference in attack success: +0.0 points
prompt-warning, paired difference in attack success, interval: [+0.0, +0.0] points
prompt-warning, paired difference in utility: +0.0 points
prompt-warning, paired difference in utility, interval: [+0.0, +0.0] points
prompt-warning, newly blocked, dev cases: 0
prompt-warning, newly let through, dev cases: 0
```

On dev, the warning changed nothing the scorers can see. Its paired difference in attack success is +0.0 points, and its utility, 93.3% (14 of 15), matches the undefended run's 93.3% (14 of 15).

A zero on the tuned split is not evidence that the warning works. It says that this wording did nothing on this set. [Hines et al.](https://arxiv.org/abs/2403.14720), researchers at Microsoft, report a 2024 arXiv preprint in which an added instruction about prompt injection gave almost no benefit for GPT-3.5-Turbo, and a modest one for another model. That preprint used GPT-family models and synthetic documents, so it sets an expectation for this book and does not replace its measurement.

On held-out, the warning moves the wrong way. Its utility cost is -6.7 points, and the interval on that difference, [-20.0, +0.0] points, reaches zero at its upper end. Dev showed no utility cost for the warning, and held-out does. The attack-success interval runs from below zero to above it, so the warning shows no attack reduction the book can claim.

**Working rule:** Run a warning on the held-out split before you credit it, and count its benign cost next to any gain. Keep it as one layer only when its held-out attack-success interval excludes zero. A zero on the tuned split is a reason to run held-out, not a result.

## Delimiters and spotlighting {#delimiters-and-spotlighting}

Spotlighting is the name [Hines et al.](https://arxiv.org/abs/2403.14720) give to transforms of untrusted text that give the model a signal of where the text came from. The preprint describes three: delimiting, [datamarking](#datamarking) and [encoding](#encoding). The idea is that a model which can tell the staff member's words from a tool's words has a better chance of following only the first.

### Delimiters {#delimiters-alone}

Delimiters wrap each untrusted segment in markers, and the system prompt says what the markers mean. Hines et al. report a beneficial effect from delimiters, smaller than datamarking's. On dev, this book's delimiters left utility where the undefended run had it, at 93.3% (14 of 15).

Attack success's paired difference was -1.7 points, with an interval of [-5.0, +0.0] points. That interval reaches zero at its upper end, so the dev run does not show a reduction.

On held-out, the paired difference in attack success is +3.3 points, with an interval of [-3.3, +10.0] points that includes zero. Held-out shows no effect either way, and its point estimate is above zero, where dev's was below. Utility's paired difference is +0.0 points.

The markers have a known weakness. Hines et al. note that an adversary who knows the delimiters can write them into their own text, and the variant's docstring in the book's code says the same. No example in this chapter measures that, so the weakness is stated here and not shown.

**Working rule:** Use delimiters to show the model where untrusted text starts and stops, and don't count them as a control on what the model does. A reduction seen on dev counts only if held-out repeats it.

### Datamarking {#datamarking}

Datamarking replaces every whitespace character in the untrusted text with a marker character, and the system prompt names the marker. The model reads the marked text, so the change is visible to the model and not only to the harness. Hines et al. report a larger effect than delimiting's, and no detrimental effect on task performance for GPT-3.5-Turbo on their benchmarks.

On dev, datamarking lowered attack success, and its paired interval excludes zero: the difference is -6.7 points, with an interval of [-13.3, -1.7] points.

On held-out, the reduction does not hold. The paired difference in attack success is -5.0 points, with an interval of [-11.7, +1.7] points that includes zero. Utility's paired difference is -13.3 points, with an interval of [-33.3, +0.0] points, which also includes zero. The preprint's finding of no cost is about GPT-3.5-Turbo on its benchmarks. Here the held-out utility point estimate is lower, and its interval includes zero. This book shows neither a cost nor its absence.

Datamarking also changes what an [input detector](#a-classifier-guard) reads. [Chapter 5](#false-alarms-on-real-text) says where to run the detector because of it.

**Working rule:** Measure datamarking's utility on held-out before you accept it, and read its held-out attack-success interval with the dev one beside it. A reduction that appears only on dev is a dev result.

### Encoding {#encoding}

Encoding replaces each untrusted segment with an encoded form, here the base64 encoding of its UTF-8 bytes. The system prompt says that tool output is base64 and is data, and that it must not be followed. Third-party tool definitions are untrusted too, so this variant encodes them as well. Encoding therefore changes two things at once, the tool results and the tool definitions, and the book's runs cannot tell the two apart. The model must decode the text before it can read it.

[Hines et al.](https://arxiv.org/abs/2403.14720) report that encoding gave the lowest attack success of the three transforms, and that only the most capable models decode the text with high fidelity. GPT-3.5-Turbo's task performance suffered on encoded text in their experiments. Those were GPT-family models in 2024, not a 4B open-weight model, and their encoding did not change tool definitions, which this variant does. The book's encoded runs also lose utility, and they don't show why. Model size is one possible cause, and the runs do not separate it from encoding the tool results or from encoding the tool definitions. There is no encoded run on the 0.6B model, and no run that varies model size with encoding on.

On dev, encoding moved attack success further than any other variant did. It blocked 7 cases that the undefended run let through, so no defence on this set can lower attack success by more than the undefended run's rate. The paired difference is -11.7 points, with an interval of [-20.0, -5.0] points, which excludes zero.

The cost falls on the benign tasks, where encoding's paired difference in utility is -26.7 points, with an interval of [-46.7, -6.7] points. The runs don't show whether the model decoded the encoded text or ignored it. The traces show only that no attack goal was met.

On held-out, encoding's attack-success result holds. The paired difference is -11.7 points, with an interval of [-20.0, -3.3] points that lies wholly below zero. It is the only held-out attack-success interval that does. The utility cost grows, and its paired difference on the held-out benign tasks is -53.3 points. Because the variant encodes the tool definitions, that cost comes from the definitions, the tool results, or both, and this chapter's runs do not say which.

**Working rule:** An encoding can stop every attack in a set and still leave the assistant unable to do its work. Read its utility on the held-out benign tasks before you call it a defence. A cost that large is a reason to look for a design that keeps untrusted text away from the model that acts, which is the subject of [Chapter 8](#dual-llm).

## Repeating the request {#repeating-the-request}

After the last tool result, this variant repeats the staff member's request as a user turn, directly before the model's reply. The idea is that the request is the last thing the model reads before it answers, so the model keeps the staff member's goal in view. AgentDojo tests the same design under the name repeat prompt. Its authors report that it raised benign utility and lowered targeted attack success with GPT-4o, and they say it is "unlikely to withstand adaptive attacks" ([AgentDojo](https://arxiv.org/abs/2406.13352), an arXiv preprint, v3, with no venue on the copy). That is the benchmark's result, on its own tasks and model. This book's runs point the other way on utility.

On dev, the repeated request has the largest utility cost of the five variants. Its paired difference in utility is -73.3 points, with an interval of [-93.3, -46.7] points. Its paired difference in attack success is -5.0 points, with an interval of [-11.7, +1.7] points that includes zero, so the lower point estimate is not a reduction this run can show.

The next example looks for the cause among the dev benign tasks whose check needs an action: a message sent for an outbox check, or a visit booked for a booking check.

Example `prompt-repeat-why` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""On the dev benign tasks, the repeated request makes the model end more tasks in a text reply that lacks the action the
task's check needs. The line the prose rests on is `prompt-repeat, text reply without the needed call`, beside the
same count on the undefended baseline.
"""
from lib import cases, runs  # lib first: threads and seeds are fixed here


def needed_tools(check):
    """The side-effecting tools a task's check needs: an outbox check needs send_message, a booking check book_visit.
    A check that only reads the reply needs none."""
    if check["type"] == "all":  # a compound check needs every tool its parts need
        return set().union(*(needed_tools(part) for part in check["checks"]))
    return {"outbox_to": {"send_message"}, "booking": {"book_visit"}}.get(check["type"], set())


def text_without_action(task, trace):
    """True when the task needs an action, the trace's last event is a text reply, and no needed call was made."""
    needed = needed_tools(task.check)
    acted = any(trace.tool_calls(name) for name in needed)  # the calls the scorer would look for
    return bool(needed) and trace.events[-1].kind == "reply" and not acted


def count(recording, variant=None):
    """The dev benign tasks that need an action, and how many of them ended in text without it."""
    tasks = cases.load_tasks("dev")
    traces = runs.replay_tasks(recording, tasks, variant=variant)
    needing = [t for t in tasks if needed_tools(t.check)]
    return sum(text_without_action(t, traces[t.id]) for t in needing), len(needing)


def main():
    # The repeat variant is replayed with its row of lib/variants.py; the baseline with none, so a wrong hook fails the hash check.
    base_hits, needing = count("baseline-dev")
    repeat_hits, repeat_needing = count("prompt-repeat-dev", "prompt-repeat")
    assert needing == repeat_needing, "the same tasks must need an action in both runs"
    assert repeat_hits > base_hits, "the repeated request should cost more calls than the baseline"  # the prose's claim
    print(f"tasks that need an action, dev benign: {needing}")
    print(f"baseline, text reply without the needed call: {base_hits} of {needing}")
    print(f"prompt-repeat, text reply without the needed call: {repeat_hits} of {needing}")


if __name__ == "__main__":
    main()
```

Output:

```text
tasks that need an action, dev benign: 12
baseline, text reply without the needed call: 0 of 12
prompt-repeat, text reply without the needed call: 11 of 12
```

Of the 12 tasks that need an action, the undefended run ended in a text reply without the needed call on 0 of 12. With the repeated request, it did so on 11 of 12. The two runs are one recording each, on the same tasks, and differ only in the repeated request. The model answers in text instead of making the call, and the task's check fails.

On held-out, the repeat's utility cost is -33.3 points, with an interval of [-53.3, -13.3] points that excludes zero. Its attack-success paired difference is -1.7 points, with an interval of [-8.3, +5.0] points that includes zero.

**Working rule:** Before you repeat the request, count the tasks that need an action and check that the run still makes those calls. A repeat that stops the action also stops the task, and the utility number is what shows it.

## What each costs {#what-each-costs}

Each defence has two costs: the benign tasks it loses, and the tokens it adds to the prompts. The first is in the paired numbers above. The second is counted in the next example, on the dev benign tasks, with the Qwen3 tokeniser from the pinned files. That tokeniser matched the 4B model's own count on the book's probe texts when control tokens are read as control tokens. Each variant's count is summed over that task's model calls in the variant's own run. A run that makes fewer calls has fewer prompts to add to, so a total can fall because the run did less and not because its text is shorter.

Example `prompt-cost-tokens` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3), passing in Edition 2026.11.4:

```python
"""The tokens each variant adds to the prompts it is given, on the 15 dev benign tasks, summed over each task's model
calls. Each variant also prints the part of that sum that falls on the tool definitions, the rest of it, and the number
of model calls its run made, because a run that makes fewer calls has fewer prompts to add to. The line the prose rests
on is `prompt-encode, added prompt tokens in tool definitions, median`, beside its total. The tokens are counted with
lib/tokens.py on the pinned Qwen3-0.6B tokenizer, which matches the 4B model's count on the baseline prompts (notes/probes.md, P-1).
"""
import statistics

from lib import cases, defences, harness, replay, runs, tokens, tools  # lib first: threads and seeds are fixed here

VARIANTS = {"prompt-datamark": defences.prompt_datamark, "prompt-delimiters": defences.prompt_delimiters,
            "prompt-encode": defences.prompt_encode, "prompt-repeat": defences.prompt_repeat,
            "prompt-warning": defences.prompt_warning}


def added_tokens(recording, defence, world, tasks):
    """Per task ID: the tokens the defence added to the prompts the model was given, summed over its model calls; the
    part of that sum on the tool definitions; and the number of model calls."""
    model = replay.ReplayModel(recording)  # the variant's own recording, so each reply is the one it was given
    totals = {}
    for task in tasks:
        growths = []  # per call: the growth of the whole prompt, and of its tool definitions

        def transform(segments):  # the hook sees each prompt before the change, so the growth is the defence's own
            changed = defence(segments)
            growths.append(tokens.growth(segments, changed, harness.prompt_text))
            return changed

        hooks = harness.Hooks(name="measure", transform_input=transform)
        system = harness.system_text(runs.TEMPLATE, task.acting_user, world)
        harness.run_episode(task.id, task.text, task.acting_user, model, system=system,
                            state=tools.ToolState.new(task.acting_user), hooks=hooks,
                            assistant_prefix=harness.ASSISTANT, max_tokens=runs.ANSWER_TOKENS)
        totals[task.id] = tokens.sum_growth(growths)
    return totals


def main():
    world, tasks = cases.load_world(), cases.load_tasks("dev")
    assert len(tasks) == 15, "the dev benign tasks have changed"
    for name in sorted(VARIANTS):
        totals = added_tokens(f"{name}-dev", VARIANTS[name], world, tasks)
        added, schemas, elsewhere, calls = tokens.columns(totals)  # sorted by task ID, so the order is fixed
        print(f"{name}, added prompt tokens, median: {statistics.median(added):.0f}")
        print(f"{name}, added prompt tokens, maximum: {max(added)}")
        print(f"{name}, added prompt tokens in tool definitions, median: {statistics.median(schemas):.0f}")
        print(f"{name}, added prompt tokens elsewhere, median: {statistics.median(elsewhere):.0f}")
        print(f"{name}, model calls, median: {statistics.median(calls):.0f}")


if __name__ == "__main__":
    main()
```

Output:

```text
prompt-datamark, added prompt tokens, median: 418
prompt-datamark, added prompt tokens, maximum: 555
prompt-datamark, added prompt tokens in tool definitions, median: 195
prompt-datamark, added prompt tokens elsewhere, median: 223
prompt-datamark, model calls, median: 3
prompt-delimiters, added prompt tokens, median: 220
prompt-delimiters, added prompt tokens, maximum: 220
prompt-delimiters, added prompt tokens in tool definitions, median: 0
prompt-delimiters, added prompt tokens elsewhere, median: 220
prompt-delimiters, model calls, median: 3
prompt-encode, added prompt tokens, median: 1625
prompt-encode, added prompt tokens, maximum: 1647
prompt-encode, added prompt tokens in tool definitions, median: 1419
prompt-encode, added prompt tokens elsewhere, median: 206
prompt-encode, model calls, median: 3
prompt-repeat, added prompt tokens, median: 66
prompt-repeat, added prompt tokens, maximum: 85
prompt-repeat, added prompt tokens in tool definitions, median: 0
prompt-repeat, added prompt tokens elsewhere, median: 66
prompt-repeat, model calls, median: 2
prompt-warning, added prompt tokens, median: 183
prompt-warning, added prompt tokens, maximum: 183
prompt-warning, added prompt tokens in tool definitions, median: 0
prompt-warning, added prompt tokens elsewhere, median: 183
prompt-warning, model calls, median: 3
```

Measured as the median over the dev benign tasks, each defence adds these tokens to a task's prompts, summed over its calls:

- the warning, 183 tokens;
- delimiters, 220 tokens;
- datamarking, 418 tokens, up to 555 on the largest task;
- repeating the request, 66 tokens;
- encoding, 1625 tokens, up to 1647 on the largest task.

The warning adds the same note on every call, so its total scales with the number of calls. Here every dev task's total was 183, the same as its median.

The repeated request has the lowest total, and part of the reason is its run. Its median run makes 2 model calls, against 3 for the warning's run. A task whose run ends in text after one tool result makes fewer calls, so it carries fewer reminders.

Encoding has the largest total, and most of it is the tool definitions. Those are encoded on every call, along with the tool results. The median of encoding's added tokens on the tool definitions is 1419, and the rest, the tool results and the system note, has a median of 206. Datamarking also marks the whitespace in the tool definitions, which accounts for 195 of its median. So the encoding count is the cost of the variant as built, which encodes the definitions by design, and not only of base64 on the tool results.

The token cost does not rank the defences the way the utility cost does. In this run the repeat is the cheapest in tokens, and it has the largest utility cost on dev. On held-out, encoding costs the most utility, a paired difference of -53.3 points against the repeat's -33.3 points, and it is also the largest cost in tokens, measured on dev. A ranking from the tuned split can change on the held-out split, so a cost comparison needs both.

Figure 4.1 draws each run's attack success along the bottom and its utility up the side, so a defence that lowers attack success without costing utility sits toward the upper left. The undefended run, the baseline, is at 11.7% (7 of 60) attack success and 93.3% (14 of 15) utility. The warning's point is on top of it, since the two runs have the same counts. Each bar is that run's own 95% interval. The paired intervals in the sections above compare each defence with the baseline case by case, and they decide which differences this run shows.

*Figure 4.1. Each run's dev attack success against its dev utility, with 95% bootstrap intervals.*

![On the dev split, encoding alone stops every attack, and encoding and repeating the request give up the most benign tasks](https://rollingedition.ai/books/securing-llm-applications-and-agents/2026.11.4/figures/prompt-defence-tradeoff.svg)

Example `figure-prompt-defence-tradeoff` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · matplotlib 3.11.2 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Draw each prompt defence's dev attack success against its dev utility, with the undefended baseline and 95% bootstrap intervals.
The lines name each run's attack success and utility with their counts, which the prose rests on.
"""
from lib import cases, runs, scorers, stats  # lib first: threads and seeds are fixed here
from lib.figures import ACCENT, INK, new_figure, save

# Label places in data units, beside their points. The warning's point is the baseline's, so one label names both.
LABELS = {"baseline": (15.5, 88.0), "prompt-delimiters": (1.5, 101.0), "prompt-datamark": (6.5, 76.0),
          "prompt-encode": (1.2, 57.0), "prompt-repeat": (8.5, 12.0)}
# Plain names, the words the chapter's prose uses. The run IDs stay in the printed lines and the bindings.
NAMES = {"baseline": "undefended and warning", "prompt-delimiters": "delimiters", "prompt-datamark": "datamarking", "prompt-encode": "encoding", "prompt-repeat": "repeating the request"}


def run_dev(name):
    """Utility of the 15 dev benign tasks and attack success of the 60 dev cases, in ID order, as 1s and 0s."""
    recording, variant = ("baseline-dev", None) if name == "baseline" else (f"{name}-dev", name)
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, variant=variant)
    case_traces = runs.replay_cases(recording, attacks, variant=variant)
    utility = [float(scorers.utility(t, traces[t.id])) for t in sorted(benign, key=lambda t: t.id)]
    success = [float(scorers.attack_success(c, case_traces[c.id])) for c in sorted(attacks, key=lambda c: c.id)]
    return utility, success


def rate(label, flags):
    """Print a rate with its counts and bootstrap interval, as the paired example does; return it in points."""
    lo, hi = stats.bootstrap_mean(flags)  # the same interval the paired example prints, from the same seed
    print(f"{label}: {stats.pct(int(sum(flags)), len(flags))}\n{label}, interval: {stats.interval_pct(lo, hi)}")
    return 100 * sum(flags) / len(flags), 100 * lo, 100 * hi


def main():
    fig, ax = new_figure(height=3.8)
    # the baseline last, so its ink bars sit on the warning's identical ones
    for name in ("prompt-warning", "prompt-delimiters", "prompt-datamark", "prompt-encode", "prompt-repeat", "baseline"):
        utility, success = run_dev(name)
        x, y = rate(f"{name}, attack success, 60 dev cases", success), rate(f"{name}, utility, 15 dev benign tasks", utility)
        color = INK if name == "baseline" else ACCENT  # the baseline in ink, each defence in the accent
        _, caps, bars = ax.errorbar(x[0], y[0], xerr=[[x[0] - x[1]], [x[2] - x[0]]], yerr=[[y[0] - y[1]], [y[2] - y[0]]], fmt="o",
                                    color=color, capsize=2, elinewidth=0.9, zorder=3 if name == "baseline" else 2,
                                    markersize=9 if name == "prompt-warning" else 5,  # the warning's ring shows around the baseline's point
                                    markerfacecolor="none" if name == "prompt-warning" else color)
        if name == "prompt-delimiters": [a.set_linestyle("--") for a in (*caps, *bars)]  # its bars lie on the baseline's
        if name in LABELS:  # the warning has no label of its own: the baseline's label says it coincides
            ax.annotate(NAMES[name], (x[0], y[0]), xytext=LABELS[name][:2], ha="left", va="center", color=color,
                        arrowprops=dict(arrowstyle="-", color=INK, linewidth=0.5, shrinkA=4, shrinkB=2))
    assert run_dev("prompt-warning") == run_dev("baseline"), "the warning's point is the baseline's"  # the prose says so
    ax.set(xlabel="attack success, percent of 60 dev cases", ylabel="utility, percent of 15 dev benign tasks",
           xlim=(-1, 25), ylim=(0, 105))
    save(fig, "prompt-defence-tradeoff")


if __name__ == "__main__":
    main()
```

Output:

```text
prompt-warning, attack success, 60 dev cases: 11.7% (7 of 60)
prompt-warning, attack success, 60 dev cases, interval: [5.0%, 20.0%]
prompt-warning, utility, 15 dev benign tasks: 93.3% (14 of 15)
prompt-warning, utility, 15 dev benign tasks, interval: [80.0%, 100.0%]
prompt-delimiters, attack success, 60 dev cases: 10.0% (6 of 60)
prompt-delimiters, attack success, 60 dev cases, interval: [3.3%, 18.3%]
prompt-delimiters, utility, 15 dev benign tasks: 93.3% (14 of 15)
prompt-delimiters, utility, 15 dev benign tasks, interval: [80.0%, 100.0%]
prompt-datamark, attack success, 60 dev cases: 5.0% (3 of 60)
prompt-datamark, attack success, 60 dev cases, interval: [0.0%, 11.7%]
prompt-datamark, utility, 15 dev benign tasks: 86.7% (13 of 15)
prompt-datamark, utility, 15 dev benign tasks, interval: [66.7%, 100.0%]
prompt-encode, attack success, 60 dev cases: 0.0% (0 of 60)
prompt-encode, attack success, 60 dev cases, interval: [0.0%, 0.0%]
prompt-encode, utility, 15 dev benign tasks: 66.7% (10 of 15)
prompt-encode, utility, 15 dev benign tasks, interval: [40.0%, 86.7%]
prompt-repeat, attack success, 60 dev cases: 6.7% (4 of 60)
prompt-repeat, attack success, 60 dev cases, interval: [1.7%, 13.3%]
prompt-repeat, utility, 15 dev benign tasks: 20.0% (3 of 15)
prompt-repeat, utility, 15 dev benign tasks, interval: [0.0%, 40.0%]
baseline, attack success, 60 dev cases: 11.7% (7 of 60)
baseline, attack success, 60 dev cases, interval: [5.0%, 20.0%]
baseline, utility, 15 dev benign tasks: 93.3% (14 of 15)
baseline, utility, 15 dev benign tasks, interval: [80.0%, 100.0%]
figure: figures/prompt-defence-tradeoff.svg
```

The two whose paired intervals show a dev reduction, datamarking and encoding, both sit below the baseline's utility: encoding stops every attack, at 0.0% (0 of 60), and keeps 66.7% (10 of 15) of the benign tasks. The repeat sits far below the rest, at 20.0% (3 of 15), with a bar from [0.0%, 40.0%] that 15 tasks make wide.

These counts describe these prompts, this tokeniser and this set of short documents. Real tool results are longer, and a deployed model's tokeniser may split the same text differently. Count the tokens with the tokeniser of the model you deploy, on the prompts it will read, and not with the numbers printed here.

**Working rule:** Count each defence's tokens with the deployed model's tokeniser, on the prompts it will read, and count the calls its run makes. Put each cost beside its benign and attack results. If two defences lower attack success by the same amount, keep the one that costs fewer benign tasks and fewer tokens.

## A smaller model {#a-smaller-model}

The undefended 0.6B model looks safer than the 4B model on the dev split, and that is worth a closer look, because it shows how a safety number can come from what a model does rather than from what it resists. The smaller model is Qwen3-0.6B, pinned like the 4B model and run with thinking off. The example sets the two models beside each other on the same dev tasks and cases.

Example `prompt-small-model` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""The 0.6B model against the 4B baseline on the dev split: utility, attack success, their paired differences, and how
many attack cases each model never read the carrier's content in. The line the prose rests on is
`never read the carrier, 0.6B`, set beside the 4B's count, with the left-out count on its own line: a weaker model looks safer partly because it reads less.
"""
from lib import cases, harness, replay, report, runs, scorers, stats, tools, variants  # lib first: threads and seeds are fixed here


def run_dev(recording, prefix):
    """The dev benign tasks and cases of one recording, undefended: utility by task ID, and by case ID the case,
    whether its attack succeeded, and its trace. The prefix is the generation prompt the recording was made with."""
    model, tasks = replay.ReplayModel(recording), {t.id: t for t in cases.load_tasks()}

    def episode(item_id, text, user, state):  # the book's system prompt for this user, as the recording had it
        system = harness.system_text(runs.TEMPLATE, user, cases.load_world())
        return harness.run_episode(item_id, text, user, model, system=system, state=state,
                                   assistant_prefix=prefix, max_tokens=runs.ANSWER_TOKENS)

    utility = {t.id: scorers.utility(t, episode(t.id, t.text, t.acting_user, tools.ToolState.new(t.acting_user)))
               for t in cases.load_tasks("dev")}
    attack = {}
    for case in cases.load_cases("dev"):  # each attack rides on the benign task it names
        base = tasks[case.task]
        state = tools.ToolState.new(base.acting_user, carrier=case.carrier, injection=case.injection)
        trace = episode(case.id, base.text, base.acting_user, state)
        attack[case.id] = (case, scorers.attack_success(case, trace), trace)
    return utility, attack


def main():
    big_u, big = run_dev("baseline-dev", variants.VARIANTS["baseline"].prefix)  # the 4B model
    small_u, small = run_dev("baseline-dev-06b", variants.VARIANTS["baseline-06b"].prefix)  # thinking off
    ids, cids = sorted(big_u), sorted(big)
    for m, u, a in (("4B", big_u, big), ("0.6B", small_u, small)):
        report.rate_lines(f"{m}, utility, 15 dev benign tasks", [u[t] for t in ids], f"{m}, utility interval")
        report.rate_lines(f"{m}, attack success, 60 dev cases", [a[c][1] for c in cids], f"{m}, attack success interval")

    # Paired differences, 0.6B minus 4B: one number per task or case, so each counts once.
    for name, before, after in (("utility", [big_u[t] for t in ids], [small_u[t] for t in ids]),
                                ("attack success", [big[c][1] for c in cids], [small[c][1] for c in cids])):
        diffs = stats.paired_differences(before, after)
        print(f"0.6B minus 4B, paired difference in {name}: {100 * sum(diffs) / len(diffs):+.1f} points, "
              f"interval {stats.interval_points(*stats.bootstrap_mean(diffs))}")

    # The carrier count, over the cases whose carrier a tool returns. Tool-description cases are left out.
    counted = [c for c in cids if big[c][0].carrier["kind"] in report.CARRIER_TOOL]
    never = {}
    for m, a in (("4B", big), ("0.6B", small)):
        never[m] = sum(report.never_read(big[c][0], a[c][2]) for c in counted)
        print(f"never read the carrier, {m}: {never[m]} of {len(counted)}")
    print(f"tool-description cases left out: {len(cids) - len(counted)}")
    assert never["0.6B"] > never["4B"], "the weaker model should read the carrier less often"  # the prose's claim


if __name__ == "__main__":
    main()
```

Output:

```text
4B, utility, 15 dev benign tasks: 93.3% (14 of 15)
4B, utility interval: [80.0%, 100.0%]
4B, attack success, 60 dev cases: 11.7% (7 of 60)
4B, attack success interval: [5.0%, 20.0%]
0.6B, utility, 15 dev benign tasks: 20.0% (3 of 15)
0.6B, utility interval: [0.0%, 40.0%]
0.6B, attack success, 60 dev cases: 0.0% (0 of 60)
0.6B, attack success interval: [0.0%, 0.0%]
0.6B minus 4B, paired difference in utility: -73.3 points, interval [-93.3, -53.2] points
0.6B minus 4B, paired difference in attack success: -11.7 points, interval [-20.0, -5.0] points
never read the carrier, 4B: 0 of 53
never read the carrier, 0.6B: 24 of 53
tool-description cases left out: 7
```

On dev, the 0.6B model looks safer than the 4B model. Its attack success is 0.0% (0 of 60), and against the 4B model on the same tasks and cases, its paired difference in attack success is -11.7 points, interval [-20.0, -5.0] points. Its paired difference in utility is -73.3 points, interval [-93.3, -53.2] points.

The utility gap is expected: the smaller model does less of the office's work. The attack gap needs a closer look. In each counted attack case, the carrier is the tool result that holds the injected text, and each carrier kind has one tool that returns its full content. The counts ask whether the model called that tool. The 0.6B model never called it in 24 of 53 counted cases. The 4B model never called it in 0 of 53 counted cases. The tool-description cases are left out of both counts, because their text sits in every prompt's tool schema and cannot go unread, and there are 7 of them.

A case the model never reads cannot reach its goal through that text, so the 0.6B model's zero is partly a fact about what it does. The model also completed 20.0% (3 of 15) of the benign tasks. Its zero therefore cannot be read as resistance: it fails to act on the tasks it was given, whether or not an action was injected. A defence that made the 4B model read less would show the same kind of zero. The count of reads, reported beside the rate, is what separates the two cases.

**Working rule:** Before you credit a model or a defence with a lower attack success, count how often it read the carrier. Report that count beside the rate. A rate that comes from text the model never read is a count of what the model did, and it is not evidence that the model resists.

## The held-out run {#the-held-out-run}

Each defence's wording was fixed on the dev split, and each then ran once on the held-out split. Both splits are reported, each claim names its split, and a dev result that held-out doesn't repeat is said not to hold. The dev results were used to choose the wording, so they can't also show that it works. Held-out is a second sample of cases from the same attack families, and one run per defence is all the book takes from it. The intervals are the honest measure of how much one run can move. The held-out undefended run, which is lower than dev's, is reported in [chapter 3](#undefended-baseline).

The held-out example gives each defence's paired attack-success difference, with its interval:

- The warning: -1.7 points, interval [-8.3, +3.3] points.
- Delimiters: +3.3 points, interval [-3.3, +10.0] points.
- Datamarking: -5.0 points, interval [-11.7, +1.7] points.
- Repeating the request: -1.7 points, interval [-8.3, +5.0] points.
- Encoding: -11.7 points, interval [-20.0, -3.3] points.

Only encoding's attack-success difference excludes zero on held-out, and it does so at the utility cost described above. The held-out run confirms the two large utility costs, of encoding and of repeating the request, whose intervals exclude zero. It does not confirm the smaller costs of the warning and of datamarking, whose intervals reach zero. The warning's cost appeared only on held-out.

Dev was not kinder to every defence. It overstated the delimiters' attack reduction and the repeat's utility cost, and it understated the utility cost of the warning, of datamarking and of encoding. A claim drawn from dev alone would have been wrong for each of them, and in different directions.

Held-out is also a finite resource. A second held-out run after a wording change is a second look at the split, and the result would no longer be held out. If a held-out run shows a defence failing, the fix goes back to dev, and the held-out split is then spent for that wording. Keep a count of how many times each defence has been run on held-out, and report it with the result.

These results hold for one fixed attack set and one model, and the attacks are static: the same cases, in the same wording, every time. [Nasr et al., 2025, *The Attacker Moves Second*](https://arxiv.org/abs/2510.09023), a preprint that is not peer-reviewed as far as its copy shows, searched for attacks against published defences that had reported low static attack success, with the search run on AgentDojo. Its adaptive attacks broke most of them. The list it reports as broken includes spotlighting and prompt sandwiching, the name for the design this chapter calls repeating the request. The preprint's static results were low and its adaptive results were high. A static zero in this chapter is therefore a result for this set and no more. [Chapter 11](#the-gap-to-the-fixed-set) tests two of them, datamarking and encoding, against an attacker that adapts, on this book's own model.

**Working rule:** Report each defence's held-out paired attack-success difference with its interval, and claim a reduction only where that interval excludes zero. Don't tune again on the held-out split. A static result holds for the static set, and it meets an [adaptive attacker](#adaptive-attacker) in chapter 11.
