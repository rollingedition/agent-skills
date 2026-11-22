"""What the attacker did with its turns, and what it was shown: replays the same chains as `adaptive-round-count`. The
lines the prose rests on are `attacker turns repeating the previous injection` and `feedback keys`, which is only
whether the goal was reached and, per call, the tool name and its decision.
"""
from lib import adaptive, cases, replay  # lib first: threads and seeds are fixed here

RECORDING = "adaptive-round-5"


def main():
    selected = adaptive.select_cases(cases.load_cases("dev"), 12)
    manifest = replay.ReplayModel(RECORDING).manifest
    chains = {(d, c.id): adaptive.replay_loop(RECORDING, c, d) for d in sorted(adaptive.DEFENCES) for c in selected}

    # Only the attacker's turns (rounds 1 on) can repeat; a turn that returns its previous injection tries nothing new.
    turns = sum(len(rs) - 1 for rs in chains.values())
    repeats = sum(r.injection == prev.injection for rs in chains.values() for prev, r in zip(rs, rs[1:]))
    one_idea = sum(len(rs) > 1 and len({r.injection for r in rs[1:]}) == 1 for rs in chains.values())
    print(f"attacker turns repeating the previous injection: {repeats} of {turns}")
    print(f"chains whose attacker turns hold one distinct injection: {one_idea} of {len(chains)}")

    # The feedback each round gave the attacker: these keys and decisions only, never a reply, result or argument.
    rounds = [r for rs in chains.values() for r in rs]
    assert all(set(r.feedback) == {"goal_reached", "calls"} for r in rounds), "feedback carries another field"
    calls = [call for r in rounds for call in r.feedback["calls"]]
    assert all(set(call) == {"tool", "decision"} for call in calls), "a call carries another field"
    print("feedback keys: calls, goal_reached")
    print(f"decisions seen: {', '.join(sorted({call['decision'] for call in calls}))}")

    # Totals against the recording. Its manifest's `target_episodes` counts the target's model turns, not episodes.
    rows = replay.ReplayModel(RECORDING)._rows
    target_items = {item for item, _, _ in rows if item.endswith("/target")}
    target_turns = sum(1 for item, _, _ in rows if item.endswith("/target"))
    print(f"target episodes replayed: {len(rounds)}")
    print(f"attacker turns replayed: {turns}")
    print(f"target model turns recorded: {target_turns}")
    assert len(rounds) == len(target_items), "target episodes differ from the recording's target items"
    assert target_turns == manifest["target_episodes"], "target model turns differ from the manifest"
    assert turns == manifest["attacker_calls"], "attacker turns differ from the manifest"


if __name__ == "__main__":
    main()
