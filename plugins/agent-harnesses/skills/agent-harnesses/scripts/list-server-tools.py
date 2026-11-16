"""Opens the two example servers over stdio and prints the protocol revision the SDK negotiates with each, with the
tools each offers. The harness offers only the tools its policy names, under harness names, as the gate classes them.
The printed line `docs protocol revision: 2026-07-28` is the revision the docs server and the SDK settle on, and the
last printed line, `offered to the model: [...]`, is the list the model is offered."""
from lib.mcp_tools import POLICY, SERVERS, connected, mcp_tools
from lib.permissions import Gate, library_copy, scripted
from mcp.types import LATEST_PROTOCOL_VERSION

with connected(SERVERS) as conns, library_copy() as library:
    print(f"SDK latest revision: {LATEST_PROTOCOL_VERSION}")
    for conn in conns:
        # the default mode of mcp.Client: the server and the SDK settle on the newest revision both speak
        print(f"{conn.server.name} protocol revision: {conn.protocol}")
        print(f"{conn.server.name} tools: {[t.name for t in conn.tools]}")
    offered = mcp_tools(conns, Gate(library, scripted(), classes=POLICY))
    print(f"offered to the model: {[t.name for t in offered]}")
assert {conn.protocol for conn in conns} == {LATEST_PROTOCOL_VERSION} == {"2026-07-28"}
assert "docs__reset_index" not in [t.name for t in offered]
