"""Hand each handed-off message to a person, with the stand-in's recorded answer as a labelled suggestion.
The point rests on the "team returned for a handed-off message" line and the "suggestions right" line."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
# the threshold is read from the manifest, not typed here
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
test = router_lib.read_rows("test")
standin = router_lib.standin_rows()  # a dict from test row index to the stand-in's answer, for the rows it answered
rows, handed = [], []
# simulated=False keeps weeks 1 and 2 only: the replay belongs to the watch, not to this example
for weekly_rows, _, confs in router_lib.watch_weeks(model, tokenizer, threshold, simulated=False):
    rows += weekly_rows
    handed += [i for i, c in zip(weekly_rows, confs) if router_lib.handoff(c, threshold)]

# the list of records stands in for the person's queue, which the book does not build
# the suggestion is None where the stand-in has no recorded answer, and the team is always None
queue = [{"index": i, "team": None, "suggestion": standin[i]["label"] if i in standin else None} for i in handed]
suggested = [r for r in queue if r["suggestion"] is not None]
right = sum(r["suggestion"] == test[r["index"]][1] for r in suggested)  # index 1 of a test row is its gold team

print(f"messages routed: {len(rows)}")
print(f"handed off by the router: {len(handed)}/{len(rows)} ({100 * len(handed) / len(rows):.1f}%)")
print(f"sent to a person: {len(queue)}/{len(handed)}")
print(f"suggestions attached: {len(suggested)}/{len(handed)}")
print(f"suggestions right: {right}/{len(suggested)}")
print(f"team returned for a handed-off message: {sum(r['team'] is not None for r in queue)}")
