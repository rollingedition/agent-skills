"""Two servers and the harness's own tool set each offer a read_file. Each gets its own name, each call reaches the
server it came from, and the names that would clash are refused. The printed line `bare names the servers offer` shows
the clash, `names the model sees` shows the prefixed list, and the three `refused, ...` lines print the refusals."""
from lib.mcp_tools import POLICY, SERVERS, Server, connected, harness_name, mcp_tools, refusal, workspace
from lib.permissions import Gate, library_copy, scripted
from lib.tools import V1, ToolSet

with connected(SERVERS) as conns, workspace() as ws, library_copy() as library:
    tools = mcp_tools(conns, Gate(library, scripted(), classes=POLICY))
    bare = sorted(t.name for conn in conns for t in conn.tools)
    names = sorted([t.name for t in V1.tools] + [t.name for t in tools])
    print(f"bare names the servers offer: {bare}")
    print(f"names the model sees: {names}")
    print(f"names: {len(names)}")
    print(f"distinct: {len(set(names))}")
    assert len(set(names)) == len(names)
    print(f"refused, the review's pair: {refusal(lambda: harness_name('docs', '__read_file'))}")
    print(f"refused, the same name from docs_: {refusal(lambda: harness_name('docs_', '_read_file'))}")
    two_docs = [SERVERS[0], Server("docs", SERVERS[1].script)]
    print(f"refused, two servers named docs: {refusal(lambda: connected(two_docs).__enter__())}")
    tool_set = ToolSet("mcp", "", 1, tools)
    docs = tool_set.call(ws, "docs__read_file", {"path": "docs/format.md"})
    tracker = tool_set.call(ws, "tracker__read_file", {"path": "issue-8/log.txt"})
    print(f"docs__read_file reaches the docs server: {'format_quantity' in docs.text}")
    print(f"tracker__read_file reaches the tracker server: {'2 passed' in tracker.text}")
    assert "format_quantity" in docs.text and "2 passed" in tracker.text
