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
