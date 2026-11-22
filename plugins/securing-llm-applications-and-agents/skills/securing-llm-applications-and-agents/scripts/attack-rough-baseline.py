"""The undefended assistant on the rough set, replayed from the rough-baseline recording.

The chapter's first measured claim rests on the attack success line for the 20 cases: the share of attack
cases in which the goal is met on the trace, with its bootstrap interval. The count of lookups for the targeted
tenant shows that private data reached the model's context even where the attack failed.
"""
from lib import cases, report, runs, scorers, stats  # lib first: threads and seeds are fixed here


def main():
    world = cases.load_world()
    benign, attacks = runs.replay_set("rough-baseline")
    # Utility under attack: the benign task still gets its answer although the message was injected.
    utility_attack = {cid: scorers.utility(base, trace) for cid, (case, base, trace) in attacks.items()}
    success = {cid: scorers.attack_success(case, trace) for cid, (case, base, trace) in attacks.items()}

    report.rate_lines("utility, 10 benign tasks", [benign[t] for t in sorted(benign)])
    report.rate_lines("utility under attack, 20 cases", [utility_attack[c] for c in sorted(utility_attack)])
    report.rate_lines("attack success, 20 cases", [success[c] for c in sorted(success)])

    for style in sorted({case.style for case, _, _ in attacks.values()}):
        ids = sorted(cid for cid, (case, _, _) in attacks.items() if case.style == style)
        print(f"attack success, style {style}: {stats.pct(sum(success[c] for c in ids), len(ids))}")

    # The count the chapter's private-data point rests on: attack cases with a lookup of the targeted unit.
    # A lookup by unit is the way the model gets the tenant's private fields into its context.
    looked = [report.looked_up_target(case, trace, world) for case, _, trace in attacks.values()]
    print(f"lookup of the targeted tenant, attack cases: {sum(looked)} of {len(looked)}")

    # One trace, by tool name and host only, so a reader can see the pattern the chapter describes.
    print(f"tool calls, case r-01: {runs.tool_sequence(attacks['r-01'][2])}")


if __name__ == "__main__":
    main()
