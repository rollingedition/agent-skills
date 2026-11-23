"""Replay incident-day message 16297 with the live contacts server, inside the injected timeout window. Each attempt of
find_contact is its own execute_tool span. The first raises MCPError with code -32001, the SDK's code for a read timeout,
which the MCP spec does not assign: that span ends ERROR, with error.type MCPError and an exception event. The retry starts
2.5 s later, times out too, and the tool step gives up."""
from lib.dayrun import run_day_traced
from lib.tools import TIMEOUT_CODE

traced = run_day_traced("2026-12-09", ["16297"])  # the incident day, with the live server inside its window
outcome = traced.runs[0].outcome
attempts = sorted((r for r in traced.spans if r["name"] == "execute_tool find_contact"),
                  key=lambda r: r["attributes"]["ambrewick.attempt"])
injected = [r for r in traced.server if r["name"] == "tools/call find_contact" and "ambrewick.incident.id" in r["attributes"]]
first, second = attempts
assert len(attempts) == 2 and outcome.source == "model"  # the retry times out too, and the answer comes from the model
assert all(a["status"] == "ERROR" and a["attributes"]["error.type"] == "MCPError" for a in attempts)
assert first["attributes"]["ambrewick.mcp.error_code"] == TIMEOUT_CODE
assert len(injected) == 2 and all(r["attributes"]["ambrewick.incident.injected"] is True for r in injected)
print("injected incident, ID:", injected[0]["attributes"]["ambrewick.incident.id"])
print("attempts of find_contact:", len(attempts))
print("attempt 1, status and error.type:", first["status"], first["attributes"]["error.type"])
print("attempt 1, error code:", first["attributes"]["ambrewick.mcp.error_code"])
print("attempt 1, exception event:", first["events"][0]["attributes"]["exception.type"].rsplit(".", 1)[-1])
print("attempt 1, time:", f"{(first['end_ns'] - first['start_ns']) / 1e9:.1f} s")  # the 2.0 s timeout
print("attempt 2 starts after attempt 1:", f"{(second['start_ns'] - first['start_ns']) / 1e9:.1f} s")  # 2.0 s + 0.5 s
print("tool step, time:", f"{(second['end_ns'] - first['start_ns']) / 1e9:.1f} s")
