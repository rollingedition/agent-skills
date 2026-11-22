"""The same 20 cases and 10 benign tasks with the outbound allowlist enforced, from the rough-allowlist recording.

The chapter's defence claim rests on the paired difference in attack success: the change, per case, from the
undefended run to the allowlisted run, with its bootstrap interval. The benign rate is printed, and an assertion
checks that the allowlist lost no benign task that passed at baseline. The lookups of the targeted tenant are
counted, to show that private data still entered the context under the rule.
"""
from collections import Counter

from lib import cases, report, runs, scorers, stats  # lib first: threads and seeds are fixed here


def main():
    base_benign, base_attacks = runs.replay_set("rough-baseline")  # no hooks: the undefended run
    allow_benign, allow_attacks = runs.replay_set("rough-allowlist", runs.allowlist_hooks())

    # The benign tasks: the allowlist must not lose one. Checked here, not printed.
    assert all(allow_benign[t] or not base_benign[t] for t in base_benign), "allowlist lost a benign task"

    allow_utility_attack = {cid: scorers.utility(base, trace) for cid, (case, base, trace) in allow_attacks.items()}
    base_success = {cid: scorers.attack_success(case, trace) for cid, (case, _, trace) in base_attacks.items()}
    allow_success = {cid: scorers.attack_success(case, trace) for cid, (case, _, trace) in allow_attacks.items()}

    report.rate_lines("utility, 10 benign tasks", [allow_benign[t] for t in sorted(allow_benign)])
    report.rate_lines("utility under attack, 20 cases", [allow_utility_attack[c] for c in sorted(allow_utility_attack)])
    report.rate_lines("attack success, 20 cases", [allow_success[c] for c in sorted(allow_success)])

    # Lookups of the targeted tenant under the rule: the allowlist stops the send, not the read.
    world = cases.load_world()
    looked = [report.looked_up_target(case, trace, world) for case, _, trace in allow_attacks.values()]
    print(f"lookup of the targeted tenant, attack cases: {sum(looked)} of {len(looked)}")

    # The paired table: each case is in exactly one of the four cells, by its success with and without the allowlist.
    ids = sorted(base_success)
    cell = {(True, True): "both succeed", (True, False): "baseline only",
            (False, True): "allowlist only", (False, False): "neither succeeds"}
    counts = Counter(cell[(base_success[c], allow_success[c])] for c in ids)
    for name in sorted(cell.values()):
        print(f"paired, {name}: {counts[name]} of {len(ids)}")

    # The paired difference, allowlist minus baseline, per case, bootstrapped over the 20 cases.
    diffs = stats.paired_differences([base_success[c] for c in ids], [allow_success[c] for c in ids])
    lo, hi = stats.bootstrap_mean(diffs)
    print(f"paired difference in attack success, allowlist minus baseline: {100 * sum(diffs) / len(diffs):+.1f} points")
    print(f"paired difference, interval: {stats.interval_points(lo, hi)}")

    # Calls refused by the allowlist across the 20 attack runs, by tool name. Benign runs are not counted here.
    refused = [name for _, _, trace in allow_attacks.values() for name in runs.refused_tools(trace)]
    if not refused:
        print("calls refused: 0")
    for tool_name in sorted(set(refused)):
        print(f"calls refused, {tool_name}: {refused.count(tool_name)}")


if __name__ == "__main__":
    main()
