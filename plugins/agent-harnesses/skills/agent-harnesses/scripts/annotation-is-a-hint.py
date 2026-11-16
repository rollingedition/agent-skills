"""The docs server marks delete_page read-only. The harness still classes it as a change, so each call asks first.
The printed lines `server marks delete_page read-only: True` and `harness class of docs__delete_page: change` set the
server's mark beside the harness's class. A tool the policy does not name is not offered, even when the server marks
it read-only: `harness class of docs__reset_index: never`, and `reset_index: error: unknown tool: docs__reset_index`
is the refusal of a direct call. The line `forced call: error: not a tool this harness runs` is the gate's refusal of
a tool object the policy does not name, whatever its runner would do."""
from lib.mcp_tools import POLICY, SERVERS, AnyArgs, connected, mcp_tools, workspace
from lib.permissions import Gate, classify, library_copy, scripted
from lib.tools import Tool, ToolResult, ToolSet

with connected(SERVERS) as conns, workspace() as ws, library_copy() as library:
    remote = {t.name: t for t in conns[0].tools}  # conns[0] is the docs server: SERVERS lists docs first
    print(f"server marks delete_page read-only: {remote['delete_page'].annotations.read_only_hint}")
    print(f"harness class of docs__delete_page: {classify('docs__delete_page', POLICY)}")
    print(f"server marks reset_index read-only: {remote['reset_index'].annotations.read_only_hint}")
    print(f"harness class of docs__reset_index: {classify('docs__reset_index', POLICY)}")
    # the scripted gate answers the first proposal no and the second yes
    gate = Gate(library, scripted((False, "not this page"), (True, "remove it")), classes=POLICY)
    tools = mcp_tools(conns, gate)
    print(f"offered: {[t.name for t in tools]}")
    tool_set = ToolSet("mcp", "", 1, tools)  # ToolSet(name, system prompt, step cap, tools): one step, no prompt
    no = tool_set.call(ws, "docs__delete_page", {"path": "docs/format.md"})
    yes = tool_set.call(ws, "docs__delete_page", {"path": "docs/format.md"})
    refused = tool_set.call(ws, "docs__reset_index", {})
    print(f"first call: {no.brief}")
    print(f"second call: {yes.brief}")
    print(f"reset_index: {refused.text}")
    # a tool object the policy does not name, with a runner that would succeed; the gate wraps it, so its checks run
    probe = Tool(name="docs__reset_index", description="", args=AnyArgs, run=lambda w, a: ToolResult("ran", brief="ran"))
    forced = ToolSet("probe", "", 1, (gate.wrap(probe),)).call(ws, "docs__reset_index", {})
    print(f"forced call: {forced.brief}")
    assert forced.brief == "error: not a tool this harness runs" and "ran" not in forced.text
    assert classify("docs__delete_page", POLICY) == "change" and "docs__reset_index" not in [t.name for t in tools]
    assert no.brief == "error: not approved" and no.end == "ask_user" and "deleted" not in no.text
    assert "deleted docs/format.md" in yes.text
    assert refused.text == "error: unknown tool: docs__reset_index"
