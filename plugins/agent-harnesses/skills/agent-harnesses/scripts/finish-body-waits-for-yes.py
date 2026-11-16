"""A finish that publishes does its work only after a yes. With a no the body never runs; with a yes it runs once,
after the change is applied to the library."""
from dataclasses import replace

from lib.permissions import Gate, answer, gated, library_copy
from lib.tools import V1, ToolResult, Workspace

published = []


def finish_and_publish(ws, args):
    published.append(args.summary)
    return ToolResult("run ended", brief="finish", end="finish", summary=args.summary)


publishing = replace(V1, tools=tuple(replace(t, run=finish_and_publish) if t.name == "finish" else t
                                     for t in V1.tools))


def finish_with(yes: bool):
    with library_copy() as library, library_copy() as scratch:
        gate = Gate(library, lambda p: answer(p, yes, "decided"))
        (scratch / "unitcraft" / "n.py").write_text("N = 1\n", encoding="utf-8")
        result = gated(publishing, gate).call(Workspace(scratch), "finish", {"summary": "Publish."})
        return result, gate, (library / "unitcraft" / "n.py").exists()


no_result, _, no_added = finish_with(False)
print("no: ended", no_result.end, "| publish ran:", len(published), "| file added:", no_added)
yes_result, gate, yes_added = finish_with(True)
print("yes: ended", yes_result.end, "| publish ran:", len(published), "| file added:", yes_added)
print("applied:", gate.counts["applied"])
assert no_result.end == "ask_user" and len(published) == 1 and not no_added
assert yes_result.end == "finish" and yes_added and gate.counts["applied"] == 1
