"""Watch the router's hand-off rate week by week on a fixed, ordered sample of test_1001, against the dev baseline.
The point rests on the "drift" lines and on the "lowest confidence" and "right" lines of weeks 3 and 4, which the output
labels as a simulated replay."""

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

handed_dev, n_dev = router_lib.dev_handed_off(model, tokenizer, threshold)
base = 100 * handed_dev / n_dev
print(f"dev hand-off rate (baseline): {handed_dev}/{n_dev} ({base:.1f}%)")
print(f"drift rule: more than {router_lib.DRIFT_POINTS:.0f} points from the baseline")
print("weeks 3 and 4: simulated replay of sample messages 51 to 100")
test = router_lib.read_rows("test")
# simulated=True (the default) adds weeks 3 and 4: messages 51 to 100, lowest confidence first, ties by position
for w, (rows, preds, confs) in enumerate(router_lib.watch_weeks(model, tokenizer, threshold), 1):
    n = len(rows)
    handed = sum(router_lib.handoff(c, threshold) for c in confs)
    rate = 100 * handed / n
    # the messages the router keeps, each with its gold team: test row i holds (text, gold team)
    kept = [(p, test[i][1]) for i, p, c in zip(rows, preds, confs) if not router_lib.handoff(c, threshold)]
    right = sum(p == g for p, g in kept)
    print(f"week {w} messages: {n}")
    print(f"week {w} handed off: {handed}/{n} ({rate:.1f}%)")
    # abs makes the rule two-sided, so a fall in the rate drifts as a rise does
    print(f"week {w} drift: {'yes' if abs(rate - base) > router_lib.DRIFT_POINTS else 'no'}")
    print(f"week {w} lowest confidence: {min(confs):.3f}")
    print(f"week {w} right among messages not handed off: {right}/{len(kept)}")
