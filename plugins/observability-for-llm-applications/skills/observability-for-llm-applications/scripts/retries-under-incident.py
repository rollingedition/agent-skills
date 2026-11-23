"""What each injected window does to the calls it covers, on the incident day, run live so the contacts server applies its
faults. A timed-out find_contact is two attempts that end ERROR with MCP code -32001, the retry starting after the read
timeout and the retry delay; a refused model request is retried on the assistant's backoff. Every line here is labelled
with its window: injected, not a natural rate."""
import tomllib

from lib import inject
from lib.case import CASE_DIR
from lib.dayrun import run_day_traced
from lib.report import fmt_int, fmt_ms
from lib.tools import REQUEST_TIMEOUT_NS, RETRY_DELAY_NS

live = run_day_traced("2026-12-09")
# Spans carry no message ID, so each message is found by its trace: the root spans come in arrival order, as the runs do.
roots = sorted((row for row in live.spans if row["name"].startswith("invoke_agent")), key=lambda row: row["trace_seq"])
message_of = {root["trace_id"]: run.message.message_id for root, run in zip(roots, live.runs, strict=True)}
windows = {incident.incident_id: incident for incident in inject.load_incidents()}
schedule = {row["id"]: row for row in tomllib.loads((CASE_DIR / "incidents.toml").read_text(encoding="utf-8"))["incident"]}
finds = [row for row in live.spans if row["name"] == "execute_tool find_contact"]
refused = [row for row in live.spans if row["attributes"].get("error.type") == "RateLimitError"]


def inside(name, row):
    """Whether a span starts inside the named window (the window's virtual start, inclusive, to its end)."""
    return windows[name].start_ns <= row["start_ns"] < windows[name].end_ns


def say(name, label, value):
    """Print one labelled value for a window."""
    print(f"{name} (injected), {label}: {value}")


TIMEOUT = "inc-contacts-timeout"
# The schedule's stamps read 2026-12-09T13:00:00.000000Z, so characters 11 to 16 hold the UTC clock time.
say(TIMEOUT, "window start (UTC)", schedule[TIMEOUT]["start"][11:16])
say(TIMEOUT, "window end (UTC)", schedule[TIMEOUT]["end"][11:16])
timeouts = sorted((row for row in finds if inside(TIMEOUT, row)
                   and row["attributes"].get("error.type") == "MCPError"), key=lambda row: row["start_ns"])
assert all(row["status"] == "ERROR" and row["attributes"]["ambrewick.mcp.error_code"] == -32001 for row in timeouts)
assert all(row["end_ns"] - row["start_ns"] == REQUEST_TIMEOUT_NS for row in timeouts)  # each attempt waits the read timeout
say(TIMEOUT, "attempts that time out", fmt_int(len(timeouts)))
say(TIMEOUT, "MCP error code", timeouts[0]["attributes"]["ambrewick.mcp.error_code"])
say(TIMEOUT, "read timeout", fmt_ms(REQUEST_TIMEOUT_NS))
pairs = [(a, b) for a, b in zip(timeouts, timeouts[1:]) if a["trace_id"] == b["trace_id"]]
assert all(b["start_ns"] - a["start_ns"] == REQUEST_TIMEOUT_NS + RETRY_DELAY_NS for a, b in pairs)
say(TIMEOUT, "retries", fmt_int(len(pairs)))
say(TIMEOUT, "retry wait", fmt_ms(RETRY_DELAY_NS))
say(TIMEOUT, "retry starts after the first attempt", fmt_ms(pairs[0][1]["start_ns"] - pairs[0][0]["start_ns"]))

errors = [row for row in finds if inside("inc-mcp-error", row)]
say("inc-mcp-error", "retries", fmt_int(sum(row["attributes"]["ambrewick.attempt"] > 1 for row in errors)))

replied = [run for run in live.runs if run.outcome.source == "model" and run.message.message_id in schedule["inc-rate-limit"]["message_ids"]]
retried = [run for run in replied if any(message_of[row["trace_id"]] == run.message.message_id for row in refused)]
say("inc-rate-limit", "messages that got a reply after a refused attempt", fmt_int(len(retried)))
assert len(retried) == len(replied)  # every reply in the window came after a refusal
