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
