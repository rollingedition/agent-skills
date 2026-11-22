"""Each contractor tool's declared arguments and effect are checked against what its tool does on a fresh call: the tables it writes, and the arguments its code reads, recorded by a proxy.

The check catches a mislabelled effect (a read-only or undeclared tool that writes, or a write whose tables are not the approved ones) and a mislabelled argument list (an argument the code reads that the schema does not name, or one the schema names that the code never reads). It does not judge the text of a description: an instruction written into a description is tool poisoning, and this check does not detect it.

The point rests on the book_visit lines. The contractor's listing declares no annotations, so the check reports that book_visit writes without a declared write: an open gap, pinned here. The copy that declares a write to the approved tables agrees; the copy that claims read-only while it writes must disagree.
"""
from lib import cases, pinning, threat, tools  # lib first: threads and seeds are fixed before anything else loads

APPROVED_WRITES = {"book_visit": ("bookings", "slots")}  # the tables book_visit was approved to write, from its review
EXPECTED = {"book_visit": "disagrees", "list_slots": "undeclared"}  # the contractor's listing declares no annotations


def observed(name: str, world: cases.World, acting: str) -> tuple[list[str], list[str]]:
    """The state fields a call changes on a fresh episode, and the argument keys the tool's code reads from its args."""
    state = tools.ToolState.new(acting)  # fresh, so one call's writes are not seen by the next
    recorder = pinning.ReadRecorder(threat.sample_args(world, state)[name])
    before = threat.snapshot(state)
    tools.call_tool(name, recorder, state)
    after = threat.snapshot(state)
    return sorted(f for f in threat.STATE_FIELDS if after[f] != before[f]), sorted(recorder.read)


def check(tool: dict, world: cases.World, acting: str, approved, case: str) -> str:
    """Prints the declared and observed facts for one definition, labelled by its case, and returns its verdict."""
    name = tool["name"]
    declared = pinning.declared_effect(tool)
    writes, reads = observed(name, world, acting)
    declared_args = set(tool["parameters"])
    print(f"declared arguments, {name}, {case}: {', '.join(sorted(declared_args))}")
    print(f"observed arguments, {name}, {case}: {', '.join(reads)}")
    print(f"declared effect, {name}, {case}: {declared}")
    print(f"observed writes, {name}, {case}: {', '.join(writes) or 'none'}")
    verdict = pinning.claim_verdict(declared, writes, approved) if declared_args == set(reads) else "disagrees"
    print(f"verdict, {name}, {case}: {verdict}")
    return verdict


def main():
    world = cases.load_world()
    acting = cases.load_tasks()[0].acting_user  # any staff member; the sample calls do not depend on the role
    server = pinning.load_json_strict((cases.DATA / "contractor.json").read_text(encoding="utf-8"))["tools"]

    for tool in sorted(server, key=lambda t: t["name"]):
        verdict = check(tool, world, acting, APPROVED_WRITES.get(tool["name"], ()), "contractor")
        assert verdict == EXPECTED[tool["name"]], f"{tool['name']}: {verdict}"

    # A copy that declares a write to the approved tables: the claim agrees with what the call does.
    book = next(t for t in server if t["name"] == "book_visit")
    declared_write = dict(book, annotations={"readOnlyHint": False})
    assert check(declared_write, world, acting, APPROVED_WRITES["book_visit"], "declared write") == "agrees"

    # The same copy with a second table written that was not approved: it disagrees.
    assert check(declared_write, world, acting, ("bookings",), "second table") == "disagrees"

    # The copy that claims read-only while the same call still writes: it disagrees.
    lying = dict(book, annotations={"readOnlyHint": True})
    assert check(lying, world, acting, APPROVED_WRITES["book_visit"], "read-only copy") == "disagrees"


if __name__ == "__main__":
    main()
