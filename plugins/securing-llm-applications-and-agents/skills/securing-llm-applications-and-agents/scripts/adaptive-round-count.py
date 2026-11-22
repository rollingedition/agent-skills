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
