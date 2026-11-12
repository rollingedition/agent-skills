"""Choose the hand-off threshold on the dev split: the lowest one on a 0.01 grid whose messages not handed off
are at least 0.90 accurate. Then show the trade-off at three thresholds. Dev only; test_200 is never used here."""

import json

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest_threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
TARGET = 0.90

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])
n = len(dev)
chosen = router_lib.choose_threshold(preds, golds, confs, TARGET)

print(f"dev messages: {n}")
print(f"target accuracy on messages not handed off: {TARGET:.2f}")
print(f"chosen threshold: {chosen:.2f}")
print(f"threshold in manifest: {manifest_threshold:.2f}")
print(f"chosen threshold matches manifest: {'yes' if chosen == manifest_threshold else 'no'}")
for t in sorted({0.50, chosen, 0.90}):
    r = router_lib.metrics(preds, golds, confs, t)
    print(f"threshold {t:.2f} handed off: {r['handed_off']}/{n} ({r['handoff_rate']:.1%})")
    print(f"threshold {t:.2f} accuracy on messages not handed off: {r['correct_not_handed_off']}/{r['not_handed_off']} ({r['accuracy_not_handed_off']:.1%})")
