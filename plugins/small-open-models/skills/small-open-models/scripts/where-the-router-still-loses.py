"""Where the router still loses: test_200 scored for the router and the stand-in. The prose rests on the count of
messages the stand-in gets right and the router wrong, and on the wrong answers the router sends as answers.
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
# The threshold chapter 5 chose on dev, as the adapter's manifest records it.
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]
# Keyed by test row index, not by position in the sample, so each lookup uses the sample's row numbers.
answers = router_lib.standin_rows()
test = router_lib.read_rows("test")  # (text, label index) per row
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]  # index 1 is the gold team, as an index
standin_preds = [answers[i]["label"] for i in sample]  # the label is the team's index, the same form as the gold label
tokenizer, model = router_lib.load_classifier(ADAPTER / "adapter")
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])
n = len(sample)
router_right = [p == g for p, g in zip(preds, golds)]
standin_right = [p == g for p, g in zip(standin_preds, golds)]
handed_off = [router_lib.handoff(c, threshold) for c in confs]  # true below the threshold; a NaN confidence is handed off too
lost = [i for i in range(n) if standin_right[i] and not router_right[i]]
sent_wrong = sum(not r and not h for r, h in zip(router_right, handed_off))  # wrong and not handed off: what a caller receives
print(f"messages on test_200: {n}")
print(f"router banking77-lora-v1 correct: {sum(router_right)}/{n} ({sum(router_right) / n:.1%})")
print(f"stand-in correct: {sum(standin_right)}/{n} ({sum(standin_right) / n:.1%})")
print(f"router threshold from manifest: {threshold:.2f}")
print(f"router handed off: {sum(handed_off)}/{n} ({sum(handed_off) / n:.1%})")
print(f"right for the stand-in, wrong for the router: {len(lost)}/{n} ({len(lost) / n:.1%})")
print(f"of those, handed off by the router: {sum(handed_off[i] for i in lost)}/{len(lost)}")
print(f"wrong for the router and sent as an answer: {sent_wrong}/{n} ({sent_wrong / n:.1%})")
print(f"right for the router, wrong for the stand-in: {sum(r and not s for r, s in zip(router_right, standin_right))}/{n}")
