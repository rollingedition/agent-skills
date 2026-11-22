"""Which goals each least-privilege defence can see: the baseline's successful attacks that each defence stops, by goal.
The lines the prose rests on are `enforce-filter, baseline successes blocked, all goals`, read against the baseline's
total, and the two gated-call lines, which say where the approval step could have acted.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")
GATED = ("send_message", "book_visit")  # the side-effecting tools the approval step covers


def successes(name, keep=None):
    """Attack success by case ID on the 60 dev cases, for the baseline or one defence (runs.replay_dev). With `keep`,
    a dict is filled with each case's trace."""
    attacks = cases.load_cases("dev")
    assert len(attacks) == 60, "the dev split has changed"  # the count the prose names
    traces = runs.replay_dev(name, (), attacks)[1]  # no benign tasks: only the attack traces are scored here
    if keep is not None:
        keep.update(traces)
    return {c.id: scorers.attack_success(c, traces[c.id]) for c in attacks}


def main():
    goal = {c.id: c.goal for c in cases.load_cases("dev")}
    base_traces = {}
    base = successes("baseline", keep=base_traces)
    won = sorted(c for c in base if base[c])  # the baseline's successes: the only cases a defence can block
    print(f"baseline successes, 60 dev cases: {len(won)}")
    gated = [c for c in won if any(base_traces[c].tool_calls(t) for t in GATED)]  # successes that called a gated tool
    print(f"baseline successes that made a gated call, all goals: {len(gated)} of {len(won)}")
    for name in DEFENCES:
        after = successes(name)
        blocked = [c for c in won if not after[c]]
        if name == "enforce-approval":  # the approval step gates side effects only, so it can block a success only through one
            assert not blocked, "the approval step blocked a baseline success"
            print(f"{name}, baseline successes with a gated call blocked, all goals: "
                  f"{sum(c in blocked for c in gated)} of {len(gated)}")
        # one line per goal, with the baseline successes in that goal
        rows = report.count_by(won, lambda c: goal[c], lambda c: c in blocked)
        report.print_counts(f"{name}, baseline successes blocked, goal", rows)
        print(f"{name}, baseline successes blocked, all goals: {len(blocked)} of {len(won)}")


if __name__ == "__main__":
    main()
