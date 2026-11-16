"""Put the student banking77-distilled-v1 beside its control banking77-gold-1000-v1, which has the same recipe and the
same 1,000 training rows but gold labels, on the same test_200 messages. The point rests on the two counts of messages
each adapter gets right that the other gets wrong, which need no threshold; both adapters are scored live, and nothing
is trained."""

import json
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"
DEV_N = 500  # the first 500 of the dev messages, as student-recorded-adapter uses: the time budget under two CPUs
print(f"dev messages used: {DEV_N} of {len(router_lib.read_sample('dev'))}")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
# sample holds test row positions; field 1 of a test row is its gold team, field 0 its text
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]

runs = {}
for name, folder in [("banking77-distilled-v1", "distill-student"), ("banking77-gold-1000-v1", "gold-same-rows")]:
    tokenizer, model = router_lib.load_classifier(RECORDED / folder / "adapter")
    threshold, reached = router_lib.dev_threshold(model, tokenizer, target=0.90, n=DEV_N)
    print(f"{name} dev threshold reaching 0.90 accuracy not handed off: {'yes' if reached else 'no'}")
    print(f"{name} threshold chosen on dev: {threshold:.2f}")
    preds, confs = router_lib.classify(model, tokenizer, texts)
    router_lib.print_copy_report(name, preds, confs, golds, threshold)
    runs[name] = [p == g for p, g in zip(preds, golds)]

# dict order is insertion order: the student first, then the control
student, control = runs.values()
n = len(golds)
print(f"test_200 messages the student gets right and the control gets wrong: {sum(s and not c for s, c in zip(student, control))}/{n}")
print(f"test_200 messages the control gets right and the student gets wrong: {sum(c and not s for s, c in zip(student, control))}/{n}")

# Recipe sizes from the recorded manifests: the student and its control share rows and steps;
# the human-labelled adapter does not. Its manifest names its row count train_rows, not rows, which is why rows_key differs.
for name, folder, rows_key in [
    ("banking77-distilled-v1", "distill-student", "rows"),
    ("banking77-gold-1000-v1", "gold-same-rows", "rows"),
    ("banking77-lora-v1", "lora-full", "train_rows"),
]:
    settings = json.loads((RECORDED / folder / "manifest.json").read_text())["settings"]
    print(f"{name} training rows: {settings[rows_key]}")
    print(f"{name} training steps: {settings['steps']}")
