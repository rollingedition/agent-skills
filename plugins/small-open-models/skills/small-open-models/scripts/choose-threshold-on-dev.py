"""Find the hand-off threshold on dev by the manifest's rule, then check it against the manifest's value.
Read the chosen threshold beside the three threshold lines. test_200 is not read here."""

import json

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest_threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
TARGET = 0.90  # the book's target accuracy on messages not handed off: a choice the book makes, not one the data sets

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])  # batches by length to pad less; results come back in dev order
n = len(dev)
chosen = router_lib.choose_threshold(preds, golds, confs, TARGET)  # the rule lives in router_lib: the lowest 0.01 grid value that meets TARGET; None if no value meets it, and the prints below would then fail

print(f"dev messages: {n}")
print(f"target accuracy on messages not handed off: {TARGET:.2f}")
print(f"chosen threshold: {chosen:.2f}")
print(f"threshold in manifest: {manifest_threshold:.2f}")
print(f"chosen threshold matches manifest: {'yes' if chosen == manifest_threshold else 'no'}")  # both come from the same 0.01 grid, so equal means the same threshold
for t in sorted({0.50, chosen, 0.90}):  # 0.50 is chapter 1's placeholder; a set drops the chosen value if it is one of the other two
    r = router_lib.metrics(preds, golds, confs, t)
    print(f"threshold {t:.2f} handed off: {r['handed_off']}/{n} ({r['handoff_rate']:.1%})")
    print(f"threshold {t:.2f} accuracy on messages not handed off: {r['correct_not_handed_off']}/{r['not_handed_off']} ({r['accuracy_not_handed_off']:.1%})")
