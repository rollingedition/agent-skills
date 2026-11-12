"""Compare the stand-in's recorded answers with the recorded adapter's live predictions on test_200.
Both models score the same 200 messages. The stand-in's threshold is chapter 1's placeholder."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
STANDIN_THRESHOLD = 0.5  # Placeholder from chapter 1. Chapter 5 chooses the threshold on dev.
ADAPTER = router_lib.HERE / "data" / "recorded" / "lora-full"

with open(router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl") as f:
    answers = {row["index"]: row for row in map(json.loads, f)}
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
standin_preds = [answers[i]["label"] for i in sample]
standin_confs = [math.exp(answers[i]["logprob"]) for i in sample]

tokenizer, model = router_lib.load_classifier(ADAPTER / "adapter")
adapter_preds, adapter_confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])

standin = router_lib.metrics(standin_preds, golds, standin_confs, STANDIN_THRESHOLD)
adapter = router_lib.metrics(adapter_preds, golds, adapter_confs, threshold)
n = standin["n"]
s_right = [p == g for p, g in zip(standin_preds, golds)]
a_right = [p == g for p, g in zip(adapter_preds, golds)]

print(f"messages on test_200: {n}")
print(f"stand-in correct: {standin['correct']}/{n} ({standin['accuracy']:.1%})")
print(f"adapter banking77-lora-v1 correct: {adapter['correct']}/{n} ({adapter['accuracy']:.1%})")
print(f"stand-in placeholder threshold: {STANDIN_THRESHOLD:.2f}")
print(f"stand-in handed off: {standin['handed_off']}/{n} ({standin['handoff_rate']:.1%})")
print(f"adapter threshold from manifest: {threshold:.2f}")
print(f"adapter handed off: {adapter['handed_off']}/{n} ({adapter['handoff_rate']:.1%})")
print(f"right for the adapter, wrong for the stand-in: {sum(a and not s for a, s in zip(a_right, s_right))}/{n}")
print(f"right for the stand-in, wrong for the adapter: {sum(s and not a for a, s in zip(a_right, s_right))}/{n}")
