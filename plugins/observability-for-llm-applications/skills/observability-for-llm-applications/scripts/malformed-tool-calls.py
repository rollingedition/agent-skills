"""Which answer replies carry a tool call the parser cannot read, on baseline day 1 (the 4B) and the model swap (the 0.6B).
A malformed call is found by parsing the reply, because its finish reason is stop either way. The constructed replies
at the end are not recorded and never become spans: they show that the parser rejects what it should."""
import glob
import json
from pathlib import Path

from lib.assistant import MalformedToolCall, parse_tool_call
from lib.dayrun import DATA, run_day_traced
from lib.report import fmt_int


def check_answers(recording):
    """Parse every answer reply in one recording. Returns the reply count, the replies with a tool call, and the
    message IDs whose reply the parser rejects."""
    paths = sorted(glob.glob(str(DATA / recording / "calls" / "*.json")))
    calls = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    answers = sorted((call for call in calls if call["kind"] == "model" and call["step"] == "answer"),
                     key=lambda call: call["seq"])  # the recorder's sequence number, unique per request
    tool_calls, rejected = 0, []
    for call in answers:
        try:
            tool_calls += parse_tool_call(call["text"]) is not None
        except MalformedToolCall:
            rejected.append(call["message_id"])
    return len(answers), tool_calls, rejected


answers, tool_calls, rejected = check_answers("baseline-day-1")
print(f"baseline day 1 (4B), answer replies: {fmt_int(answers)}")
print(f"baseline day 1 (4B), replies with a tool call: {fmt_int(tool_calls)}")
print(f"baseline day 1 (4B), malformed tool calls: {fmt_int(len(rejected))}")
# The replay parses the same recorded texts with the same parser, so its count should agree with the parse above.
replayed = sum(run.outcome.malformed_tool_calls for run in run_day_traced("2026-12-08", live=False).runs)
print(f"baseline day 1 (4B), malformed tool calls in the replay: {fmt_int(replayed)}")
assert not rejected and replayed == 0

answers, tool_calls, rejected = check_answers("release-model-swap")
print(f"model swap (0.6B, release r2), answer replies: {fmt_int(answers)}")
print(f"model swap (0.6B, release r2), replies with a tool call: {fmt_int(tool_calls)}")  # one call tests nothing
print(f"model swap (0.6B, release r2), malformed tool calls: {fmt_int(len(rejected))}")
assert not rejected

# Constructed, not recorded: two replies a model could write, passed straight to the parser.
for label, text in {"unclosed block": '<tool_call>{"name": "find_contact", "arguments": {}',
                    "body is not JSON": "<tool_call>find the contact</tool_call>"}.items():
    try:
        parse_tool_call(text)
        raise AssertionError(f"{label} was not rejected")
    except MalformedToolCall:
        print(f"constructed reply, {label}, rejected by the parser: yes")
