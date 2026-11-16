"""Score the stand-in's recorded answers on test_40, with a placeholder hand-off threshold.
The last printed line, accuracy on messages not handed off, is the one the prose reads against the others: it is the
accuracy of the messages a team receives. No model runs here, and the answers come from the recording."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

THRESHOLD = 0.5  # Placeholder. Chapter 5 chooses the threshold on the dev split.
RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"

answers = {}
with open(RECORDING) as f:
    for line in f:
        row = json.loads(line)
        answers[row["index"]] = row

rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40")

golds = [rows[i][1] for i in sample]  # element 1 of a test row is its gold label; element 0 is its text
preds = [answers[i]["label"] for i in sample]  # the recorded label is the team's position in LABELS, as the gold is
confs = [math.exp(answers[i]["logprob"]) for i in sample]  # exp turns each recorded log-probability into a confidence

# metrics applies the hand-off rule at THRESHOLD; accuracy's denominator still includes handed-off messages
result = router_lib.metrics(preds, golds, confs, THRESHOLD)
n = result["n"]

print(f"messages: {n}")
print(f"placeholder threshold: {THRESHOLD}")
print(f"accuracy: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when the router keeps no message, so the measure is undefined
    print("accuracy on messages not handed off: not defined (0 messages not handed off)")
else:
    m = result["not_handed_off"]
    print(
        f"accuracy on messages not handed off: {result['correct_not_handed_off']}/{m} "
        f"({result['accuracy_not_handed_off']:.1%})"
    )
