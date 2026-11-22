"""The three least-privilege defences, each replayed on the 60 dev cases and 15 dev tasks and paired with the baseline.
The line the prose rests on is `enforce-filter, paired difference in attack success`, with its interval beneath it.
"""
from collections import Counter

from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")


def measure(name):
    """Utility by task ID, attack success by case ID, and refusals by tool in the attack cases, for one defence.
    The baseline is the undefended recording, replayed with no hooks. Each defence's hooks are built per episode from
    its task (lib/variants.py PLANS), so the recording's prompts are rebuilt as the recorder built them."""
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces_b, traces_a = runs.replay_dev(name, benign, attacks)
    utility = {t.id: scorers.utility(t, traces_b[t.id]) for t in benign}
    success = {c.id: scorers.attack_success(c, traces_a[c.id]) for c in attacks}
    refused_benign = Counter(t for tr in traces_b.values() for t in runs.refused_tools(tr))
    return utility, success, Counter(t for tr in traces_a.values() for t in runs.refused_tools(tr)), refused_benign


def main():
    results = {name: measure(name) for name in ("baseline",) + DEFENCES}
    base_u, base_s = results["baseline"][:2]
    case_ids, task_ids = sorted(base_s), sorted(base_u)
    before, base_util = [base_s[c] for c in case_ids], [base_u[t] for t in task_ids]
    report.rate_lines("baseline, attack success, 60 dev cases", before)
    report.rate_lines("baseline, utility, 15 dev tasks", base_util)
    assert sum(before) > 0, "the baseline has no successes to block"  # the paired measure needs some
    for name in DEFENCES:
        utility, success, refused, refused_benign = results[name]
        after, util = [success[c] for c in case_ids], [utility[t] for t in task_ids]
        report.rate_lines(f"{name}, attack success, 60 dev cases", after)
        report.rate_lines(f"{name}, utility, 15 dev tasks", util)
        report.paired(f"{name}, paired difference in attack success", before, after)
        report.paired(f"{name}, paired difference in utility", base_util, util)
        report.newly_lines(f"{name}, newly blocked, dev cases", f"{name}, newly let through, dev cases", before, after)
        # From the trace's defence events. The total prints at zero too: the filter removes tools from the prompt,
        # so the model may never name a tool it lacks, and no refusal is recorded.
        print(f"{name}, refusals in attack cases, all tools: {sum(refused.values())}")
        print(*(f"{name}, refusals in attack cases, {t}: {n}" for t, n in sorted(refused.items())), sep="\n")
        # The same defence on the benign tasks: a refusal here is a cost to a legitimate task, not a stopped attack.
        print(f"{name}, refusals in benign tasks, all tools: {sum(refused_benign.values())}",
              *(f"{name}, refusals in benign tasks, {t}: {n}" for t, n in sorted(refused_benign.items())), sep="\n")


if __name__ == "__main__":
    main()
