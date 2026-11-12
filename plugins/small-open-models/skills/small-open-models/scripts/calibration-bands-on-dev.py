"""Group the dev messages by the recorded adapter's confidence into five bands. For each band it prints the count,
the accuracy and the mean confidence, the two quantities Guo et al. (2017) compare for calibration. Dev only."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
BANDS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])

print(f"dev messages: {len(dev)}")
counted = 0
for lo, hi in BANDS:
    last = hi == 1.0
    members = [i for i, c in enumerate(confs) if lo <= c < hi or (last and c == 1.0)]
    counted += len(members)
    name = f"band {lo:.1f}-{hi:.1f}"
    print(f"{name} messages: {len(members)}")
    if members:
        correct = sum(preds[i] == golds[i] for i in members)
        print(f"{name} correct: {correct}/{len(members)} ({correct / len(members):.1%})")
        print(f"{name} mean confidence: {sum(confs[i] for i in members) / len(members):.1%}")
    else:
        print(f"{name} correct: not defined (0 messages)")
        print(f"{name} mean confidence: not defined (0 messages)")
print(f"messages in bands: {counted}")
