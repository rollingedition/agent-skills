"""Decide whether to retrain, as a rule over the weekly hand-off counts from handoff-windows.

The rule (the book's choice, not a sourced threshold): retrain when two consecutive weeks drift, that is, their
hand-off rate is more than router_lib.DRIFT_POINTS from the dev baseline. Weeks 3 and 4 are a simulated replay."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
handed_dev, n_dev = router_lib.dev_handed_off(model, tokenizer, threshold)
base = 100 * handed_dev / n_dev

drifting, run, longest = [], 0, 0
for rows, _, confs in router_lib.watch_weeks(model, tokenizer, threshold):
    rate = 100 * sum(router_lib.handoff(c, threshold) for c in confs) / len(rows)
    flag = abs(rate - base) > router_lib.DRIFT_POINTS
    drifting.append(flag)
    run = run + 1 if flag else 0
    longest = max(longest, run)
    print(f"week {len(drifting)} drift: {'yes' if flag else 'no'}")

print(f"weeks drifting: {sum(drifting)}/{len(drifting)}")
print(f"longest run of drifting weeks: {longest}")
print("rule: retrain when two consecutive weeks drift")
print("retrain trigger: " + ("fired" if longest >= 2 else "not fired"))
