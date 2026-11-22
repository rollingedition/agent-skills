"""The three least-privilege defences, each replayed on the 60 held-out cases and 15 held-out tasks and paired with the
baseline. The held-out split was not used to choose any defence or its settings, so these lines test the dev results.
The lines the prose rests on are the held-out paired differences, and the approval step's gated-call counts.
"""
from lib import cases, replay, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")
GATED = ("send_message", "book_visit")  # the side-effecting tools the approval step covers


def traces(name, benign, attacks):
    """Task traces and case traces for the baseline or one defence, replayed from its held-out recording."""
    if name == "baseline":
        return runs.replay_tasks("baseline-held-out", benign), runs.replay_cases("baseline-held-out", attacks)
    model = replay.ReplayModel(f"{name}-held-out")  # one model per recording: it reads its file once
    return (runs.replay_tasks(f"{name}-held-out", benign, variant=name, model=model),
            runs.replay_cases(f"{name}-held-out", attacks, variant=name, model=model))


def main():
    benign, attacks = cases.load_tasks("held-out"), cases.load_cases("held-out")
    assert (len(benign), len(attacks)) == (15, 60), "the held-out split has changed"  # the counts the prose names
    task_ids, case_ids = sorted(t.id for t in benign), sorted(c.id for c in attacks)
    by_task, by_case = {t.id: t for t in benign}, {c.id: c for c in attacks}

    def score(name):
        tb, ta = traces(name, benign, attacks)
        util = [scorers.utility(by_task[t], tb[t]) for t in task_ids]
        success = [scorers.attack_success(by_case[c], ta[c]) for c in case_ids]
        return util, success, ta

    base_util, before, base_traces = score("baseline")
    report.rate_lines("baseline, attack success, 60 held-out cases", before)
    report.rate_lines("baseline, utility, 15 held-out tasks", base_util)
    won = [i for i, hit in enumerate(before) if hit]  # the baseline's successes: the only cases a defence can block
    gated = [i for i in won if any(base_traces[case_ids[i]].tool_calls(t) for t in GATED)]
    print(f"baseline successes that made a gated call, held-out: {len(gated)} of {len(won)}")
    for name in DEFENCES:
        util, after, _ = score(name)
        report.rate_lines(f"{name}, attack success, 60 held-out cases", after)
        report.rate_lines(f"{name}, utility, 15 held-out tasks", util)
        report.paired(f"{name}, paired difference in attack success, held-out", before, after)
        report.paired(f"{name}, paired difference in utility, held-out", base_util, util)
        report.newly_lines(f"{name}, newly blocked, held-out cases", f"{name}, newly let through, held-out cases",
                           before, after)
        if name == "enforce-approval":
            blocked = [i for i in gated if not after[i]]  # gated successes the approval step stopped
            print(f"{name}, held-out successes that used a gated tool: {len(gated)}")
            print(f"{name}, held-out gated successes blocked: {len(blocked)}")


if __name__ == "__main__":
    main()
