"""Split the recorded compute of each model call on baseline day 1 into prefill (the prompt the model read) and generation
(the tokens it wrote), from llama.cpp's counters on the recording machine. The split is the method's output: the numbers
belong to that machine, and the method carries to other hardware. The recorder's warm-up call, made before each
process's first recorded message, is not recorded, so it is not in the split. Rates are computed from the recorded counts."""

from lib.dayrun import DATA
from lib.report import fmt_int, fmt_share

import json

rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
for step in ("route", "answer"):
    calls = [row for row in rows if row["step"] == step]
    prefill = sum(call["prefill_ns"] for call in calls)
    generation = sum(call["gen_ns"] for call in calls)
    first_chunk = sum(call["ttfc_ns"] for call in calls)
    evaluated = sum(call["tokens_evaluated"] for call in calls)   # the prompt's tokens the model read, minus cached ones
    written = sum(call["completion_tokens"] for call in calls)
    assert all(call["prefill_ns"] <= call["ttfc_ns"] for call in calls)   # the first chunk waits for the prompt
    print(f"{step} calls: {fmt_int(len(calls))}")
    print(f"{step}, prefill share of prefill plus generation: {fmt_share(prefill, prefill + generation)}")
    print(f"{step}, prefill share of time to first chunk: {fmt_share(prefill, first_chunk)}")
    print(f"{step}, prompt tokens evaluated per second of prefill, computed: {evaluated * 1e9 / prefill:.1f}")
    print(f"{step}, tokens written per second of generation, computed: {written * 1e9 / generation:.1f}")
