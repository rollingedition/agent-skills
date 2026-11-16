"""A file that is not UTF-8 text is shown by the hash of its bytes, and the yes binds to those bytes. When the copy's
bytes change after the yes, the apply is refused, even though both versions decode to the same replacement characters."""
from lib.permissions import Change, Gate, answer, digest_changes, gated, library_copy
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    (scratch / "unitcraft" / "blob.bin").write_bytes(b"DATA \xff\n")

    def swap_then_yes(proposal):
        print("shown as:", proposal.diff.split(";")[0])
        (scratch / "unitcraft" / "blob.bin").write_bytes(b"DATA \xfe\n")
        return answer(proposal, True)

    gate = Gate(library, swap_then_yes)
    result = gated(V1, gate).call(Workspace(scratch), "finish", {"summary": "Add a blob."})
    print("ended:", result.end)
    print("handoff:", result.question)
    print("applied:", gate.counts["applied"], "| blob in library:", (library / "unitcraft" / "blob.bin").exists())
    one = digest_changes([Change("x.bin", None, b"\xff")])
    two = digest_changes([Change("x.bin", None, b"\xfe")])
    print("hashes differ for \\xff and \\xfe:", one != two)
    assert result.end == "ask_user" and "changed after" in result.question and gate.counts["applied"] == 0
    assert one != two
