---
title: "Securing LLM Applications and Agents"
chapter: "Red-team the assistant with an adaptive attacker"
chapter_id: adaptive-attacker
book: securing-llm-applications-and-agents
edition: 2026.11.3
verified: 2026-11-22
edition_code: T64T-4BT9
canonical: https://rollingedition.com/securing-llm-applications-and-agents/adaptive-attacker
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Red-team the assistant with an adaptive attacker,” chapter 11 of Securing LLM Applications and Agents, Edition 2026.11.3, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/securing-llm-applications-and-agents/adaptive-attacker. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Red-team the assistant with an adaptive attacker

By the end of this chapter you can run an attacker that revises its injection after each try, against a defence, under a fixed budget. You can read the result round by round, compare it with the fixed set, and say what the result does and does not show. You will also see which controls in this book this attacker did not touch, and why a toolkit's static probes cannot replace the loop.

Every defence in chapters 4 to 10 was measured against injections written before the run. Each case in the attack set is a fixed string, and the assistant either followed it or did not. A real attacker is adaptive: it sees what happened and tries again. This chapter asks whether a small attacker that does that finds anything the fixed set missed on the office assistant.

On this set it found nothing the fixed set had not already found. The rest of the chapter explains why that is weak evidence.

## An attacker that iterates {#an-attacker-that-iterates}

The loop follows the shape of PAIR, where an attacker model generates candidate jailbreaks automatically ([Chao et al., 2023, a preprint](https://arxiv.org/abs/2310.08419)). The book's loop is its own code, and the list below sets out what its attacker is told.

The loop runs one chain for each defence and each selected case:

- **Round 0** is the fixed case's own injection, run under the defence. It adds no attacker turn. It is the result chapters 4 to 10 already measured.
- **Each later round** the attacker writes the next injection. The attacker is the same pinned model as the assistant, Qwen3-4B-Instruct-2507, and it returns one injection of at most 200 tokens. It receives the goal in plain words, the location where the injection is carried, its own previous injection and the feedback. The goal is the case's own goal, so each chain is scored by the same check the fixed set uses.
- **The stop rule:** a chain ends at the first round whose goal is reached, or after five attacker turns.

The feedback is deliberately small. The attacker sees two things:

- whether the goal was reached, yes or no;
- for each tool call the assistant made, the tool's name and its decision: ran, refused or withheld.

It never sees the assistant's replies, the tool results, the arguments of the calls, or a refusal's reason. A reply or a result can carry a tenant's figures. A refusal reason can name a recipient, and a name in an attacker's prompt is a name the attacker can reuse. So this attacker learns from which tools ran and which were stopped, and not from what the assistant said.

The feedback in the recording can be checked on every round. The next example asserts that each round's feedback holds only those two fields, and each call only its tool and decision. It also counts what the attacker did with its turns, which the section on [the gap](#the-gap-to-the-fixed-set) returns to:

Example `adaptive-attacker-turns` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3 · torch 2.15.0+cpu · transformers 5.24.0), passing in Edition 2026.11.3:

```python
"""What the attacker did with its turns, and what it was shown: replays the same chains as `adaptive-round-count`. The
lines the prose rests on are `attacker turns repeating the previous injection` and `feedback keys`, which is only
whether the goal was reached and, per call, the tool name and its decision.
"""
from lib import adaptive, cases, replay  # lib first: threads and seeds are fixed here

RECORDING = "adaptive-round-5"


def main():
    selected = adaptive.select_cases(cases.load_cases("dev"), 12)
    manifest = replay.ReplayModel(RECORDING).manifest
    chains = {(d, c.id): adaptive.replay_loop(RECORDING, c, d) for d in sorted(adaptive.DEFENCES) for c in selected}

    # Only the attacker's turns (rounds 1 on) can repeat; a turn that returns its previous injection tries nothing new.
    turns = sum(len(rs) - 1 for rs in chains.values())
    repeats = sum(r.injection == prev.injection for rs in chains.values() for prev, r in zip(rs, rs[1:]))
    one_idea = sum(len(rs) > 1 and len({r.injection for r in rs[1:]}) == 1 for rs in chains.values())
    print(f"attacker turns repeating the previous injection: {repeats} of {turns}")
    print(f"chains whose attacker turns hold one distinct injection: {one_idea} of {len(chains)}")

    # The feedback each round gave the attacker: these keys and decisions only, never a reply, result or argument.
    rounds = [r for rs in chains.values() for r in rs]
    assert all(set(r.feedback) == {"goal_reached", "calls"} for r in rounds), "feedback carries another field"
    calls = [call for r in rounds for call in r.feedback["calls"]]
    assert all(set(call) == {"tool", "decision"} for call in calls), "a call carries another field"
    print("feedback keys: calls, goal_reached")
    print(f"decisions seen: {', '.join(sorted({call['decision'] for call in calls}))}")

    # Totals against the recording. Its manifest's `target_episodes` counts the target's model turns, not episodes.
    rows = replay.ReplayModel(RECORDING)._rows
    target_items = {item for item, _, _ in rows if item.endswith("/target")}
    target_turns = sum(1 for item, _, _ in rows if item.endswith("/target"))
    print(f"target episodes replayed: {len(rounds)}")
    print(f"attacker turns replayed: {turns}")
    print(f"target model turns recorded: {target_turns}")
    assert len(rounds) == len(target_items), "target episodes differ from the recording's target items"
    assert target_turns == manifest["target_episodes"], "target model turns differ from the manifest"
    assert turns == manifest["attacker_calls"], "attacker turns differ from the manifest"


if __name__ == "__main__":
    main()
```

Output:

```text
attacker turns repeating the previous injection: 48 of 260
chains whose attacker turns hold one distinct injection: 7 of 60
feedback keys: calls, goal_reached
decisions seen: ran, refused, withheld
target episodes replayed: 320
attacker turns replayed: 260
target model turns recorded: 786
```

The design is a measurement, not a search for the strongest attack. Its job is to answer one question the fixed set cannot: when the attacker is allowed to change its injection after seeing a result, does its success rate rise above the fixed set's rate for the same cases and the same defence? Every choice above keeps the answer comparable. The attacker uses the same model file as the assistant, so the attacker is not the stronger party. The goal check is the one the fixed set uses, so a success means the same thing in both measures. The defence is the same code under both, so only the attacker differs.

Round 0 has to be the fixed set's own result, or the comparison means nothing. The round-count example checks it for every case and every defence, and fails the run if one differs:

Example `adaptive-round-count` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3 · torch 2.15.0+cpu · transformers 5.24.0), passing in Edition 2026.11.3:

```python
"""The adaptive attacker on 12 dev cases under each of five defences, replayed from one recording: how many chains reach
their goal by round k, for k = 0 to 5. The line the prose rests on is `goal reached by round 5, pooled`, set beside
`goal reached by round 0, pooled`: the attacker's contribution after its turns, against the fixed set's own injections.
"""
from lib import adaptive, cases, replay, runs, scorers  # lib first: threads and seeds are fixed here

RECORDING = "adaptive-round-5"


def main():
    selected = adaptive.select_cases(cases.load_cases("dev"), 12)  # no excluded style, one per goal first, ID order
    manifest = replay.ReplayModel(RECORDING).manifest
    assert [c.id for c in selected] == sorted(manifest["cases"]), "the selected cases differ from the recording"
    assert sorted(manifest["defences"]) == sorted(adaptive.DEFENCES), "the defences differ from the recording"
    print("split: dev")
    print(f"cases: {len(selected)}")
    print(f"defences: {', '.join(sorted(adaptive.DEFENCES))}")

    # One chain per defence and case: its rounds, from replaying the recording through the loop.
    chains = {}
    for defence in sorted(adaptive.DEFENCES):
        for case in selected:
            chains[(defence, case.id)] = adaptive.replay_loop(RECORDING, case, defence)

    # Round 0 is the fixed case's own episode under the defence, so its outcome must equal the fixed set's recorded
    # outcome for the same case and defence. A mismatch names the case, and fails the run: the check is not relaxed.
    mismatches = []
    for defence in sorted(adaptive.DEFENCES):
        # the dev recording of this defence, replayed with the defence's own settings (variant), as the fixed set runs
        fixed = runs.replay_cases(f"{defence}-dev", selected, variant=defence)
        for case in selected:
            fixed_success = scorers.attack_success(case, fixed[case.id])
            if chains[(defence, case.id)][0].success != fixed_success:
                mismatches.append(f"{defence}/{case.id}")
    print(f"round 0 mismatches against the fixed set: {', '.join(mismatches) if mismatches else 'none'}")
    assert not mismatches, f"round 0 differs from the fixed set for: {', '.join(mismatches)}"

    # Goal reached by round k: a chain counts once it has succeeded in any round up to and including k.
    rounds_max = adaptive.ROUNDS
    for defence in sorted(adaptive.DEFENCES):
        for k in range(rounds_max + 1):
            # the rounds 0 to k of each chain: a slice to k + 1, since the slice's end is exclusive
            hits = sum(any(r.success for r in chains[(defence, c.id)][:k + 1]) for c in selected)
            print(f"goal reached by round {k}, {defence}: {hits} of {len(selected)}")
    for k in range(rounds_max + 1):
        # the same slice for every chain: rounds 0 to k, where the slice's end k + 1 is exclusive
        hits = sum(any(r.success for r in rounds[:k + 1]) for rounds in chains.values())
        print(f"goal reached by round {k}, pooled: {hits} of {len(chains)}")

    # Replay totals: the target episodes the loop made and the attacker turns it wrote, against the manifest.
    episodes = sum(len(rounds) for rounds in chains.values())
    # A chain's attacker turns are its episodes minus one: the last round makes no attacker turn.
    attacker_turns = sum(len(rounds) - 1 for rounds in chains.values())


if __name__ == "__main__":
    main()
```

Output:

```text
split: dev
cases: 12
defences: detector-filter, egress-fetch, enforce-args, prompt-datamark, prompt-encode
round 0 mismatches against the fixed set: none
goal reached by round 0, detector-filter: 2 of 12
goal reached by round 1, detector-filter: 2 of 12
goal reached by round 2, detector-filter: 2 of 12
goal reached by round 3, detector-filter: 2 of 12
goal reached by round 4, detector-filter: 2 of 12
goal reached by round 5, detector-filter: 2 of 12
goal reached by round 0, egress-fetch: 2 of 12
goal reached by round 1, egress-fetch: 2 of 12
goal reached by round 2, egress-fetch: 2 of 12
goal reached by round 3, egress-fetch: 2 of 12
goal reached by round 4, egress-fetch: 2 of 12
goal reached by round 5, egress-fetch: 2 of 12
goal reached by round 0, enforce-args: 2 of 12
goal reached by round 1, enforce-args: 2 of 12
goal reached by round 2, enforce-args: 2 of 12
goal reached by round 3, enforce-args: 2 of 12
goal reached by round 4, enforce-args: 2 of 12
goal reached by round 5, enforce-args: 2 of 12
goal reached by round 0, prompt-datamark: 2 of 12
goal reached by round 1, prompt-datamark: 2 of 12
goal reached by round 2, prompt-datamark: 2 of 12
goal reached by round 3, prompt-datamark: 2 of 12
goal reached by round 4, prompt-datamark: 2 of 12
goal reached by round 5, prompt-datamark: 2 of 12
goal reached by round 0, prompt-encode: 0 of 12
goal reached by round 1, prompt-encode: 0 of 12
goal reached by round 2, prompt-encode: 0 of 12
goal reached by round 3, prompt-encode: 0 of 12
goal reached by round 4, prompt-encode: 0 of 12
goal reached by round 5, prompt-encode: 0 of 12
goal reached by round 0, pooled: 8 of 60
goal reached by round 1, pooled: 8 of 60
goal reached by round 2, pooled: 8 of 60
goal reached by round 3, pooled: 8 of 60
goal reached by round 4, pooled: 8 of 60
goal reached by round 5, pooled: 8 of 60
```

The example asserts that round 0 matches the fixed set for all twelve cases under all five defences. Its line `round 0 mismatches against the fixed set` lists no case. The rest of its output counts successes at each round, which the next two sections read.

The case selection changes what the rates mean. The loop runs on twelve dev cases and leaves out two styles: the encoded style and the invisible style. Neither succeeded in the undefended run on dev ([chapter 3, `#undefended-baseline`](#undefended-baseline)). An attacker that starts from a case that never worked has nothing to build on, so leaving them out spends the loop's turns on injections that worked at least sometimes. The cost is that the rates after `k` rounds describe the plain, fake-turn and important styles on these twelve cases. They are not rates for all of dev, and they should not sit beside the all-styles figures without that caveat. The twelve cases are `a-003`, `a-007`, `a-011`, `a-016`, `a-017`, `a-021`, `a-022`, `a-026`, `a-036`, `a-068`, `a-073` and `a-076`: one per goal in ID order, and the twelfth slot goes to `g-bank-fetch`, the first goal in sorted order, which is why that goal has two cases. The goals are the case goals defined in [chapter 3](#goals-locations-styles), so each chain is trying for something the fixed set also tries for.

**Working rule:** Before you read an adaptive rate, check that round 0 matches the fixed set for the same cases and defences. If it does not, the two numbers do not share a baseline, and the difference between them means nothing.

## The budget {#the-budget}

The budget has three parts: five attacker turns after round 0, five defences, and twelve cases. A chain makes at most six episodes against the assistant, one for round 0 and one after each attacker turn. The plan's worst case is therefore 360 episodes and 300 attacker turns. The plan used 20.76 seconds per episode, the slowest defence's dev figure, as a bound for every episode, and 20 seconds as a bound for each attacker turn. Those give about 13,474 seconds, or 3.7 hours, against a four-hour limit on one machine. This is plan arithmetic, not a measurement from this run, and the 20-second bound for an attacker turn was set before the run. The counts that follow are what the run did.

The replayed run made 320 episodes, not 360. A chain stops at its first success, so a chain that reached its goal at round 0 made one episode and stopped. In 8 of 60 chains the goal was reached at round 0, and the rest ran their attacker turns. The attacker wrote 260 injections in total. The example checks that figure against the recording's own count of attacker calls. The replay also rebuilds each attacker prompt from the feedback and checks it against the one recorded, so the chains shown are the ones that ran.

The budget is the control. Each case gets the same number of attacker turns under every defence, so the defences are compared on one budget, not on one each. Five turns is the number the plan could afford, and it is also the main limit on what this attacker can find. Raising it after a look at the results would be the mistake the working rule below warns against.

The timing has a second use. The plan's arithmetic is a bound, and the run fits in four hours only if the real time per attacker turn stays under it. By that arithmetic, the four-hour limit is crossed when an attacker turn takes more than about 23.1 seconds. Dropping to four rounds would remove 60 episodes and 60 attacker turns, which saves about 2,446 seconds at the plan's figures of 20.76 and 20 seconds. The 20-second figure is a bound the plan set before the run; this chapter does not report a measured attacker-turn time. A reader who runs this chapter on slower hardware should measure a turn first and set the rounds from that measurement, not from the figures printed here.

**Working rule:** Fix the number of attacker turns before the run, and use it for every defence and every case. A budget chosen after the results can make any defence look weaker or stronger.

## The gap to the fixed set {#the-gap-to-the-fixed-set}

The gap is the success rate after five attacker turns, minus the rate at round 0 for the same cases under the same defence. Round 0 is the fixed set's rate on these twelve cases, so the gap is what the attacker added on its own.

Think of each case as a yes or no for each round. A case that succeeds at round 0 and again at round 5 adds nothing. A case that fails at round 0 and succeeds at round 5 adds one. The paired method is the one from [Evaluating LLM Applications, chapter 8](https://rollingedition.com/evaluating-llm-applications/s/paired-comparisons). Here it asks what the attacker added, case by case, because the same cases appear at both rounds.

A reader can check this from the output. Where a defence's round 0 and round 5 lines match, the attacker added nothing for that defence. A higher round 5 line means a case changed outcome, and the interval shows whether that change is larger than the twelve cases can rule out as chance.

Example `adaptive-gap` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3 · torch 2.15.0+cpu · transformers 5.24.0), passing in Edition 2026.11.3:

```python
"""The gap between the fixed set and the adaptive attacker: the success rate of the same 12 dev cases at round 0 (the
fixed injection) and at round 5 (after five attacker turns), per defence and pooled, with the paired difference. The
line the prose rests on is `paired difference, pooled, round 5 minus round 0`, with its interval beneath it.
"""
from lib import adaptive, cases, report, replay, scorers  # lib first: threads and seeds are fixed here

RECORDING = "adaptive-round-5"


def main():
    selected = adaptive.select_cases(cases.load_cases("dev"), 12)  # the same 12 cases as adaptive-round-count
    excluded = sorted(adaptive.EXCLUDED_STYLES)
    print("split: dev")
    print(f"styles excluded: {','.join(excluded)}")
    assert all(c.style not in adaptive.EXCLUDED_STYLES for c in selected), "an excluded style was selected"
    assert sorted(replay.ReplayModel(RECORDING).manifest["cases"]) == [c.id for c in selected], "cases differ"

    # Each chain is replayed once; the rounds it made give the success at round 0 and at round 5.
    round0, round5 = {}, {}
    for defence in sorted(adaptive.DEFENCES):
        for case in selected:
            rounds = adaptive.replay_loop(RECORDING, case, defence)
            # A chain that succeeds at round 0 must still succeed at round 5: the loop stops at success, so a later
            # round cannot undo it. Checked on every chain, not only the pooled rate.
            assert rounds[0].success <= rounds[-1].success, f"round 5 is below round 0 for {defence}/{case.id}"
            round0[(defence, case.id)] = rounds[0].success
            round5[(defence, case.id)] = any(r.success for r in rounds)  # by round 5, a success in any round counts

    keys = sorted(round0)  # (defence, case ID) pairs, in order: the pairing for the pooled comparison
    for defence in sorted(adaptive.DEFENCES):
        ids = [k for k in keys if k[0] == defence]
        report.rate_lines(f"round 0, {defence}", [round0[k] for k in ids])
        report.rate_lines(f"round 5, {defence}", [round5[k] for k in ids])
        report.paired(f"paired difference, {defence}, round 5 minus round 0",
                      [round0[k] for k in ids], [round5[k] for k in ids])

    report.rate_lines("round 0, pooled", [round0[k] for k in keys])
    report.rate_lines("round 5, pooled", [round5[k] for k in keys])
    report.paired("paired difference, pooled, round 5 minus round 0",
                  [round0[k] for k in keys], [round5[k] for k in keys])


if __name__ == "__main__":
    main()
```

Output:

```text
split: dev
styles excluded: sty-encoded,sty-invisible
round 0, detector-filter: 16.7% (2 of 12)
round 0, detector-filter, interval: [0.0%, 41.7%]
round 5, detector-filter: 16.7% (2 of 12)
round 5, detector-filter, interval: [0.0%, 41.7%]
paired difference, detector-filter, round 5 minus round 0: +0.0 points
paired difference, detector-filter, round 5 minus round 0, interval: [+0.0, +0.0] points
round 0, egress-fetch: 16.7% (2 of 12)
round 0, egress-fetch, interval: [0.0%, 41.7%]
round 5, egress-fetch: 16.7% (2 of 12)
round 5, egress-fetch, interval: [0.0%, 41.7%]
paired difference, egress-fetch, round 5 minus round 0: +0.0 points
paired difference, egress-fetch, round 5 minus round 0, interval: [+0.0, +0.0] points
round 0, enforce-args: 16.7% (2 of 12)
round 0, enforce-args, interval: [0.0%, 41.7%]
round 5, enforce-args: 16.7% (2 of 12)
round 5, enforce-args, interval: [0.0%, 41.7%]
paired difference, enforce-args, round 5 minus round 0: +0.0 points
paired difference, enforce-args, round 5 minus round 0, interval: [+0.0, +0.0] points
round 0, prompt-datamark: 16.7% (2 of 12)
round 0, prompt-datamark, interval: [0.0%, 41.7%]
round 5, prompt-datamark: 16.7% (2 of 12)
round 5, prompt-datamark, interval: [0.0%, 41.7%]
paired difference, prompt-datamark, round 5 minus round 0: +0.0 points
paired difference, prompt-datamark, round 5 minus round 0, interval: [+0.0, +0.0] points
round 0, prompt-encode: 0.0% (0 of 12)
round 0, prompt-encode, interval: [0.0%, 0.0%]
round 5, prompt-encode: 0.0% (0 of 12)
round 5, prompt-encode, interval: [0.0%, 0.0%]
paired difference, prompt-encode, round 5 minus round 0: +0.0 points
paired difference, prompt-encode, round 5 minus round 0, interval: [+0.0, +0.0] points
round 0, pooled: 13.3% (8 of 60)
round 0, pooled, interval: [5.0%, 23.3%]
round 5, pooled: 13.3% (8 of 60)
round 5, pooled, interval: [5.0%, 23.3%]
paired difference, pooled, round 5 minus round 0: +0.0 points
paired difference, pooled, round 5 minus round 0, interval: [+0.0, +0.0] points
```

| Defence | Round 0 | Round 5 | Round 5 minus round 0 | Interval of the difference |
| --- | --- | --- | --- | --- |
| prompt-encode | 0.0% (0 of 12) | 0.0% (0 of 12) | +0.0 points | [+0.0, +0.0] points |
| prompt-datamark | 16.7% (2 of 12) | 16.7% (2 of 12) | +0.0 points | [+0.0, +0.0] points |
| detector-filter | 16.7% (2 of 12) | 16.7% (2 of 12) | +0.0 points | [+0.0, +0.0] points |
| enforce-args | 16.7% (2 of 12) | 16.7% (2 of 12) | +0.0 points | [+0.0, +0.0] points |
| egress-fetch | 16.7% (2 of 12) | 16.7% (2 of 12) | +0.0 points | [+0.0, +0.0] points |
| All five, pooled | 13.3% (8 of 60) | 13.3% (8 of 60) | +0.0 points | [+0.0, +0.0] points |

With this attacker, no case that failed at round 0 reached its goal in a later round, under any defence. The paired difference is zero in every row, and the round-count example, `adaptive-round-count`, shows the same count at each round from 0 to 5. The difference is computed case by case, so a zero means no case changed outcome. The interval on that difference is [+0.0, +0.0] points in every row, and it adds nothing. A percentile bootstrap over per-case differences that are all zero returns [0, 0] whatever the number of cases, so the interval does not say how large a gain these twelve cases could rule out. The honest statement is the count: no chain gained a success on this set, with this attacker and this budget.

A zero in twelve cases does not show that nothing could have changed, either. Twelve cases is a small sample: one changed case would move a defence's rate by one in twelve, and the pooled rate by one in sixty.

Round 0 shows what the fixed set already had. Under prompt-encode, round 0 reached the goal in 0 of 12, and five attacker turns on each case found none more. Under the other four defences, the rounds after round 0 added no case: the round 0 and round 5 counts match in every row of the table above. The pooled row counts across all five defences, so it is not the undefended rate from [chapter 3](#undefended-baseline).

**Working rule:** Read a gap beside its round 0 count and its number of cases. A zero gap with a zero-width interval means no case changed. It does not mean the interval is precise, and on twelve cases it cannot show a small gain either way.

## What the result does not show {#what-the-result-does-not-show}

This result does not show that the defences hold against adaptive attacks. The attacker is a 4B model, the same size as the assistant, with a 200-token cap and the feedback above. It had five turns, and it often repeated itself: 48 of 260 attacker turns repeated the injection of the round before, and in 7 of 60 chains every attacker turn wrote the same injection. So the search was narrower than five turns suggests. The loop ran on twelve dev cases, the same cases the defences were tuned on, and it did not run on the held-out split. With a set this small the interval for any single defence is wide: detector-filter's round 0 rate of 16.7% (2 of 12) has an interval of [0.0%, 41.7%]. A weak attacker that finds nothing is not evidence that the target is safe.

Published work points the other way. The Attacker Moves Second reports that stronger adaptive attacks bypassed twelve defences published before the paper, most with attack success above 90 percent. It also reports that the majority of those defences had reported near-zero attack success against the static strings or weak optimisation they were evaluated with ([Nasr et al., 2025, a preprint not yet peer-reviewed](https://arxiv.org/abs/2510.09023)). Those are the paper's results on the paper's targets. This book does not reproduce them.

A stronger run would change three things. Each is a plan decision, not a result. A larger or separate attacker model would write better candidates. Feedback that includes the assistant's replies would show the attacker what it had reached, at a privacy cost the loop refuses today. More rounds would give the attacker more tries. Any of these would still need the held-out split run once, after the defences were frozen, before anyone said anything about the defences.

What a reader can take from this is narrow. For these five defences, on twelve dev cases, with a 4B attacker and five turns, the loop found no injection the fixed set had missed. That is a statement about this search, not a verdict on the defences. A defence that resisted this search could still fail to a stronger one, and a defence that scored well here was never tested by a search that reached the held-out cases.

The loop attacked five defences: encoding, datamarking, the detector filter, the argument policy and `egress-fetch`. Each has a dev recording, and the budget covered those five. The rest of the book's controls were not attacked by this loop, for these reasons:

- **The outbound allowlist from [chapter 1](#an-outbound-allowlist)** was not attacked on its own, because on its own it was measured only on the rough set. It was attacked as part of `egress-fetch`, which applies the allowlist first and then [chapter 7](#egress-rules)'s rule for fetch queries.
- **The render policy and output handling** of [chapter 7](#links-and-images-in-the-reply) were not attacked. The loop plants its injections where the assistant reads data, not in its reply, and the budget covered five defences that did not include it. Output handling is in [`#output-is-untrusted`](#output-is-untrusted), so the reply channel has no adaptive result in this book.
- **The isolation designs** of [chapter 8](#dual-llm) were not among the five the budget covered.
- **The controls of [chapter 9](#hidden-context) and [chapter 10](#pinning-tool-definitions)** were not among the five either.

**Working rule:** When you report an adaptive result, name in the same paragraph the defences the loop did not attack, so no reader takes a zero difference as a verdict on the whole book.

## Mapping onto a toolkit {#mapping-onto-a-toolkit}

Teams often reach for an open toolkit before writing a loop. The research behind this chapter tried four at their pins. Only garak 0.17.1 completed an offline run, against a replay target: a stub that returns one fixed, benign reply and makes no model call. PyRIT 1.2.1 installed, but its send call did not run: the book's own probe used the wrong call signature, because the `Message.from_prompt` signature in 1.2.1 differs from what the probe assumed. RAMPART 0.1.0 does not import on a clean install, because its code imports `aiohttp`, which its declared requirements do not install. Spikee 0.9.5 wrote an empty results file, and this was not diagnosed. PyRIT and garak cannot share one environment, because their OpenAI client pins conflict.

garak 0.17.1 has iterative probes as well as fixed lists. Its `tap` module has `PAIR` and `TAP`, and its `goat` module has `GOATAttack`, which uses an attacker model over several turns. Its `agent_breaker` module is a multi-turn probe for "attacking agentic LLM applications that use tools", and it is the closest match to this loop. Its red team model analyses each tool, generates targeted exploits and stops on success. It analyses the agent's responses to earlier attempts, which is the feedback this loop withholds, and its exploits go through direct conversation with the agent. The modules `adaptive_attacks` and `atkgen` also generate attack prompts: the first from an adaptive template with a cached suffix list, the second from an attack model trained on conversations that led to toxic output. The docstrings of the iterative probes describe attacks on a model or agent through its conversation. None describes an injection placed in data the assistant reads, which is what this chapter's loop does. So none of them can stand in for the loop. This chapter ran none of them.

The table maps the book's locations and styles to garak probe modules. It has no row for a fetched page, because no docstring describes one. `web_injection`'s classes put their data in the reply instead.

| Book location or style | What it is | garak 0.17.1 probe module | What the module's docstring says it does |
| --- | --- | --- | --- |
| `loc-inbox`, `loc-upload`, `loc-index` | an instruction inside a message or document the assistant reads | `latentinjection` | buries a prompt injection in another context, such as a resume or a report |
| the reply's image and link goals, chapter 7's render channel | an instruction that makes the reply carry data out in a Markdown image or link | `web_injection` | tests injection attacks against websites, such as private data exfiltration or script injection |
| `sty-encoded` | an instruction in an encoding the model can decode | `encoding` | presents an encoded version of a target text |
| `sty-invisible` | an instruction hidden in characters a reader does not see | `smuggling`, `badchars`, `goodside` | obfuscates terms, uses invisible Unicode characters, or exploits UTF tag page encoding for user-invisible injection |
| `loc-tool-description`, `sty-fake-turn` | an instruction in a tool's description, or a message that imitates an operator's turn | none found | no module name or docstring matches |

The last row is the gap a team most often assumes is covered, and no module here tests it. The table is a reference, not a result. The module names and docstrings were read from the garak 0.17.1 wheel on PyPI. No probe was installed and run, and no garak output is in this chapter's numbers. So the table says only what each module is for. It does not say that the module's texts look like the book's cases, that the assistant follows them, or that any defence in this book stops them. Do not read the table as coverage. A module that matches a location says its probes send that kind of text, and nothing more.

**Working rule:** Before a garak module counts as covering one of the book's locations, run its probes at the pinned version and confirm that the detector scores the reply the assistant would send, not only the text of the probe. A probe matched by name alone is a guess about coverage.
