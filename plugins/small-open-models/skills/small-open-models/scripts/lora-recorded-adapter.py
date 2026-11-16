"""Load the recorded adapter banking77-lora-v1 and score test_200 at the threshold in its manifest; no training runs here.
Read the accuracy line with the two hand-off lines printed under it."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest = json.loads((RECORDED / "manifest.json").read_text())
threshold = manifest["handoff_threshold"]  # the threshold the recording chose on dev; this script chooses none

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")  # the base model comes from the adapter's config, at its revision in models.toml
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])  # a tie goes to the lower label index

result = router_lib.metrics(preds, golds, confs, threshold)  # a message is handed off when its confidence is below the threshold
n = result["n"]
print(f"adapter: {manifest['adapter']}")
print(f"handoff threshold from manifest: {threshold:.2f}")
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when no message is kept, so there is no accuracy to print
    print("accuracy on messages not handed off: not defined (0 messages not handed off)")
else:
    m = result["not_handed_off"]
    print(
        f"accuracy on messages not handed off: {result['correct_not_handed_off']}/{m} "
        f"({result['accuracy_not_handed_off']:.1%})"
    )
