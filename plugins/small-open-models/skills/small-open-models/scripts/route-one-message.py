"""Route the first message of test_40 from the stand-in's recorded answer, at the placeholder threshold.
No model runs here, and the message's text is never printed."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

THRESHOLD = 0.5  # Placeholder. Chapter 5 chooses the threshold on the dev split.
RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"


def route(row):
    """Return (team, confidence, handed off) for one recorded answer. The team is None when handed off."""
    confidence = math.exp(row["logprob"])
    flag = router_lib.handoff(confidence, THRESHOLD)
    return (None if flag else row["team"]), confidence, flag


with open(RECORDING) as f:
    recorded = {r["index"]: r for r in map(json.loads, f)}

first = router_lib.read_sample("test_40")[0]
team, confidence, flag = route(recorded[first])
print(f"team: {team or 'none (handed off)'}")
print(f"confidence: {confidence:.2f}")
print(f"handed off: {flag}")
