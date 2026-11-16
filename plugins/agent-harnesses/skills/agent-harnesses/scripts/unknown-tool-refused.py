"""A tool outside the harness's table is refused before its own code runs, even when its description says it only
reads. The refusal goes back to the model as text, and the tool's body never runs."""
from dataclasses import replace

from lib.permissions import Gate, classify, gated, library_copy, scripted
from lib.tools import V1, NoArgs, Tool, ToolResult, Workspace

ran = []


def reset(ws, args):  # stands in for any effect the table does not know about
    ran.append(1)
    return ToolResult("did something", brief="did something")


with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted())
    extra = Tool("reset_library", "A read-only helper.", NoArgs, reset)
    tools = gated(replace(V1, tools=V1.tools + (extra,)), gate)
    result = tools.call(Workspace(scratch), "reset_library", {})
    print("class:", classify("reset_library"))
    print("result:", result.text)
    print("body ran:", len(ran))
    print("never calls:", gate.counts["never calls"])
    assert not ran and result.text.startswith("error:") and gate.counts["never calls"] == 1
