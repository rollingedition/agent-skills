"""Score the stand-in's recorded answers on test_1001 with the three measures. No model runs.

The thresholds are chapter 1's placeholder and one above every confidence. The answers' hash is checked first.
"""

import hashlib, json, math, os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

PLACEHOLDER = 0.5  # Chapter 5 chooses the real threshold on the dev split.
ABOVE_ALL = 1.01  # Confidence is at most 1.0, so this hands off every message.
RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
manifest = json.loads((RECORDED / "manifest.json").read_text())
raw = (RECORDED / "answers.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == manifest["output_sha256"]["answers.jsonl"]

answers = {row["index"]: row for row in map(json.loads, raw.decode().splitlines())}
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_1001")
golds = [rows[i][1] for i in sample]
preds = [answers[i]["label"] for i in sample]
# Confidence is the probability llama-cpp-python returns for the constrained answer: exp of its log-probability.
confs = [math.exp(answers[i]["logprob"]) for i in sample]

n = len(sample)
first = router_lib.metrics(preds, golds, confs, PLACEHOLDER)
high = router_lib.metrics(preds, golds, confs, ABOVE_ALL)
print(f"messages: {n}")
print(f"placeholder threshold: {PLACEHOLDER}")
print(f"accuracy: {first['correct']}/{n} ({first['accuracy']:.1%})")
print(f"handed off: {first['handed_off']}/{n} ({first['handoff_rate']:.1%})")
m = first["not_handed_off"]
print(f"accuracy on messages not handed off: {first['correct_not_handed_off']}/{m} ({first['accuracy_not_handed_off']:.1%})")
print(f"threshold above every confidence: {ABOVE_ALL}")
print(f"handed off at that threshold: {high['handed_off']}/{n} ({high['handoff_rate']:.1%})")
if high["accuracy_not_handed_off"] is None:
    print("accuracy on messages not handed off at that threshold: not defined (0 messages not handed off)")
else:
    print(f"accuracy on messages not handed off at that threshold: {high['correct_not_handed_off']}/{high['not_handed_off']}")
