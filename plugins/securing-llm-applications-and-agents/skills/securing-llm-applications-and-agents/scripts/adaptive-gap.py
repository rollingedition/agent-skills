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
