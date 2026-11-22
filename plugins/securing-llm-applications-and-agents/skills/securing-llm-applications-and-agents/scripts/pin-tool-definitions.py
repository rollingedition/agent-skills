"""The contractor's two tools verify against their pins; a changed copy, a duplicate listing and an added key do not, and the listing gate offers only verified tools, frozen.

The point rests on the verdict for book_visit in the changed copy: it is "changed", so the tool is not in the list the model gets. The pins are the hashes approved when the tools were first trusted. Added keys, duplicate names and frozen copies are in third-party-bypasses.
"""
from lib import cases, pinning  # lib first: threads and seeds are fixed before anything else loads

from pathlib import Path

PINS = Path(__file__).resolve().parent / "data" / "third-party" / "pins.json"


def main():
    server = pinning.load_json_strict((cases.DATA / "contractor.json").read_text(encoding="utf-8"))["tools"]
    pins = pinning.read_pins(PINS, "contractor")
    print(f"tools offered by the server: {len(server)}")
    print(f"tools pinned: {len(pins)}")

    # Unchanged definitions verify against their pins.
    verdicts = pinning.check_pins(pins, server)
    for name in sorted(verdicts):
        print(f"verdict, unchanged definition, {name}: {verdicts[name]}")
    assert all(v == "verified" for v in verdicts.values()), "an unchanged contractor tool must verify"

    # The hash reads the fields, not the order the server wrote them in: reversed keys give the same hash.
    tool = server[0]
    reordered = dict(reversed(list(tool.items())))
    same = pinning.definition_hash(reordered) == pinning.definition_hash(tool)
    print(f"same hash with keys reordered, {tool['name']}: {same}")
    assert same

    # A rug pull, built here as a modified copy: the carrier tool's description gains the attack's sentence.
    attacks = pinning.load_json_strict((cases.DATA / "attacks.json").read_text(encoding="utf-8"))["cases"]
    case = sorted((c for c in attacks if c["location"] == "loc-tool-description" and c["split"] == "dev"),
                  key=lambda c: c["id"])[0]  # the first dev attack carried in a description; its text is never printed
    carrier_tool = case["carrier"]["tool"]
    rugged = pinning.rugged_copy(server, carrier_tool, case["injection"])
    print(f"carrier case: {case['id']}")
    print(f"changed tool: {carrier_tool}")

    changed = pinning.check_pins(pins, rugged)
    for name in sorted(changed):
        print(f"verdict, after the change, {name}: {changed[name]}")
    assert changed[carrier_tool] == "changed"

    # The listing gate: the model is offered only the tools whose verdict is verified.
    listed = [tool["name"] for tool in pinning.listable(pins, rugged)]
    print(f"tools listed to the model after the change: {', '.join(listed)}")
    assert carrier_tool not in listed and len(listed) == len(server) - 1


if __name__ == "__main__":
    main()
