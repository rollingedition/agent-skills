"""Each tool's trifecta legs, and whether removing one leg's tools leaves at most two legs (the Rule of Two), asserted
on the computed sets. The prompt's private values are checked apart, since dropping the private tools does not remove them."""
from lib import cases, threat, tools  # lib first: threads and seeds are fixed here


def main():
    legs = threat.legs_by_tool()
    total = set().union(*legs.values())
    print(f"tools checked: {len(legs)}")
    for name in sorted(legs):
        print(f"{name}, legs: {', '.join(l for l in threat.LEGS if l in legs[name]) or 'none'}")
    print(f"legs in the tool set, in total: {', '.join(l for l in threat.LEGS if l in total)}")
    # The untrusted leg comes from two sources: a result that carries outside text, or a third-party definition.
    rows = threat.table()
    from_output = sorted(n for n, r in rows.items() if r["untrusted_output"])
    from_definition = sorted(n for n, r in rows.items() if r["third_party_definition"])
    held_untrusted = sorted(n for n, held in legs.items() if "untrusted" in held)
    print(f"tools whose output carries outside text: {len(from_output)}")
    print(f"tools with a third-party definition: {len(from_definition)}")
    print(f"tools holding the untrusted leg: {len(held_untrusted)}")
    print(f"untrusted leg, from output: {', '.join(from_output)}")
    print(f"untrusted leg, from a third-party definition only: "
          f"{', '.join(n for n in held_untrusted if n not in from_output) or 'none'}")
    assert set(held_untrusted) == set(from_output) | set(from_definition), "the untrusted leg has another source"
    # A tool that holds all three legs by itself would need no second tool to be dangerous.
    whole = sorted(n for n, held in legs.items() if held == set(threat.LEGS))
    print(f"tools with all three legs: {', '.join(whole) or 'none'}")
    # The Rule of Two, per leg: remove every tool that carries the leg; the rest should carry at most two.
    for leg in threat.LEGS:
        kept, left = threat.without_leg(legs, leg)
        print(f"without the {leg} tools, legs left: {len(left)} ({', '.join(l for l in threat.LEGS if l in left)})")
        print(f"without the {leg} tools, tools kept: {', '.join(kept)}")
        assert len(left) <= 2, f"removing the {leg} tools leaves {len(left)} legs"
    # The prompt is a channel the tool list does not control: with the private tools removed, it still holds the values.
    private = {n for n, held in legs.items() if "private" in held}
    kept_schemas = tuple(t for t in tools.TOOLS if t["function"]["name"] not in private)
    print(f"private values in the prompt, with the private tools removed: "
          f"{'yes' if threat.holds_private_values(kept_schemas) else 'no'}")
    # Checks behind the claims.
    assert total == set(threat.LEGS), "the assistant has all three legs in total"
    assert whole == [], "no single tool holds all three legs"
    assert threat.holds_private_values(kept_schemas)


if __name__ == "__main__":
    main()
