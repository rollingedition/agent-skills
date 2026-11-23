"""Which model replies the runtime cut at its token cap, read from the finish reason the runtime recorded for each
request: baseline day 1 (the 4B, release r0) and the model swap (the 0.6B, release r2). A cut reply has finish reason
length. The runtime never reports tool_calls, so a reply with a tool call is not found this way (malformed-tool-calls)."""
import json
from collections import Counter

from lib.dayrun import DATA, run_day_traced
from lib.report import fmt_int


def finish_reasons(recording):
    """The finish reason of every model request in one recording, counted by step and reason."""
    rows = [json.loads(line) for line in (DATA / recording / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row["kind"] == "model"], Counter(
        (row["step"], row["finish_reason"]) for row in rows if row["kind"] == "model")

base_rows, base = finish_reasons("baseline-day-1")
for step in ("route", "answer"):
    print(f"baseline day 1, {step} requests, finish reason stop: {fmt_int(base[(step, 'stop')])}")
    print(f"baseline day 1, {step} requests, finish reason length: {fmt_int(base[(step, 'length')])}")
# The replay answers from the same recording, and its chat spans carry the finish reason in an array.
replayed = run_day_traced("2026-12-08", live=False).spans
chat = [row for row in replayed if row["name"].startswith("chat")]
reasons = Counter(reason for row in chat for reason in row["attributes"]["gen_ai.response.finish_reasons"])
print(f"baseline day 1, chat spans replayed with finish reason stop: {fmt_int(reasons['stop'])}")
assert reasons["length"] == 0 and reasons["stop"] == len(base_rows)  # the replay's spans match the recording

swap_rows, swap = finish_reasons("release-model-swap")
manifest = json.loads((DATA / "release-model-swap" / "manifest.json").read_text(encoding="utf-8"))
for step in ("route", "answer"):
    print(f"model swap (0.6B, release r2), {step} requests, finish reason length: {fmt_int(swap[(step, 'length')])}")
cut = [row for row in swap_rows if row["finish_reason"] == "length"]
print(f"model swap, answer cap in tokens: {manifest['answer_max_tokens']}")
print(f"model swap, cut answer, completion tokens: {cut[0]['completion_tokens']}")
assert len(cut) == 1 and cut[0]["step"] == "answer"  # one cut reply, and it is an answer
assert cut[0]["completion_tokens"] == manifest["answer_max_tokens"]  # cut at the cap, not at a stop token
