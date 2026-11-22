"""The detector filter at the threshold picked on dev, against the undefended baseline, on dev and on held-out. The lines
the prose rests on are `detector-filter, attack success, 60 held-out cases` with its paired difference, and the count of
benign tasks that lost a tool result to the filter. The pick is recomputed here from the dev texts, so the replay runs
the filter at the value the recording was made with.
"""
from lib import cases, defences, detector, harness, report, runs, scorers  # lib first: threads and seeds are fixed here


def run_split(split, recording, hooks=None):
    """The 15 benign tasks and 60 attack cases of one split, replayed: benign traces, utility and attack success."""
    benign, attacks = cases.load_tasks(split), cases.load_cases(split)
    assert (len(benign), len(attacks)) == (15, 60), "the split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, hooks=hooks)
    case_traces = runs.replay_cases(recording, attacks, hooks=hooks)
    return (traces, case_traces, {t.id: scorers.utility(t, traces[t.id]) for t in benign},
            {c.id: scorers.attack_success(c, case_traces[c.id]) for c in attacks})


def main():
    # The threshold is the dev pick, computed from the dev benign texts alone (plan section 21), never typed here.
    dev_records = detector.benign_split("dev")
    threshold = detector.pick_threshold(detector.score([text for _, _, text in dev_records]))
    assert threshold is not None, "no grid threshold leaves at most 1 dev benign record flagged"
    print(f"detector threshold, picked on dev: {threshold:.2f}")
    hooks = harness.Hooks(name="detector-filter", filter_tool_result=defences.detector_filter(threshold))

    for split in ("dev", "held-out"):
        _, _, base_utility, base_success = run_split(split, f"baseline-{split}")
        traces, case_traces, utility, success = run_split(split, f"detector-filter-{split}", hooks)
        tasks, cases_sorted = sorted(utility), sorted(success)
        report.rate_lines(f"detector-filter, utility, 15 {split} benign tasks", [utility[t] for t in tasks],
                          f"detector-filter, utility interval, {split}")
        report.rate_lines(f"detector-filter, attack success, 60 {split} cases", [success[c] for c in cases_sorted],
                          f"detector-filter, attack success interval, {split}")
        report.paired(f"detector-filter, paired difference in utility, {split}",
                      [base_utility[t] for t in tasks], [utility[t] for t in tasks])
        report.paired(f"detector-filter, paired difference in attack success, {split}",
                      [base_success[c] for c in cases_sorted], [success[c] for c in cases_sorted])
        # A benign task lost a tool result when its trace has a withhold event (the filter's defence event).
        lost = [t for t in tasks if any(e.kind == "defence" and e.result["decision"] == "withhold"
                                        for e in traces[t].events)]
        print(f"benign tasks with a tool result withheld, {split}: {len(lost)}")
        # A case counts as withheld when its trace has a withhold event: the filter's own record of a result it
        # withheld, not a prediction from the scores. The count is of cases with a withheld result, which can include a
        # result other than the carrier's; a tool-description carrier is never in a result, so it cannot count here.
        held = {cid for cid, trace in case_traces.items()
                if any(e.kind == "defence" and e.result["decision"] == "withhold" for e in trace.events)}
        print(f"attack cases with a tool result withheld, {split}: {len(held)}")
        print(f"attack cases with a tool result withheld and attack success, {split}: "
              f"{len(held & {c for c in cases_sorted if success[c]})}")


if __name__ == "__main__":
    main()
