"""Where the router still loses: test_200 scored for the router and the stand-in.
The stand-in's answers are recorded; the router runs live on 2 threads."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402
torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
ADAPTER = router_lib.HERE / "data" / "recorded" / "lora-full"
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]
answers = router_lib.standin_rows()
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
standin_preds = [answers[i]["label"] for i in sample]
tokenizer, model = router_lib.load_classifier(ADAPTER / "adapter")
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])
n = len(sample)
router_right = [p == g for p, g in zip(preds, golds)]
standin_right = [p == g for p, g in zip(standin_preds, golds)]
handed_off = [router_lib.handoff(c, threshold) for c in confs]
lost = [i for i in range(n) if standin_right[i] and not router_right[i]]
sent_wrong = sum(not r and not h for r, h in zip(router_right, handed_off))
print(f"messages on test_200: {n}")
print(f"router banking77-lora-v1 correct: {sum(router_right)}/{n} ({sum(router_right) / n:.1%})")
print(f"stand-in correct: {sum(standin_right)}/{n} ({sum(standin_right) / n:.1%})")
print(f"router threshold from manifest: {threshold:.2f}")
print(f"router handed off: {sum(handed_off)}/{n} ({sum(handed_off) / n:.1%})")
print(f"right for the stand-in, wrong for the router: {len(lost)}/{n} ({len(lost) / n:.1%})")
print(f"of those, handed off by the router: {sum(handed_off[i] for i in lost)}/{len(lost)}")
print(f"wrong for the router and sent as an answer: {sent_wrong}/{n} ({sent_wrong / n:.1%})")
print(f"right for the router, wrong for the stand-in: {sum(r and not s for r, s in zip(router_right, standin_right))}/{n}")
