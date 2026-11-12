"""Score test_200 with the float32 adapter, its int8 copy and the copy with the head in int8, at the recorded threshold.
Prints counts and rates only: accuracy, hand-offs, and how many predictions and hand-off decisions change."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]

tokenizer, float_model = router_lib.load_classifier(RECORDED / "adapter")
float_preds, float_confs = router_lib.classify_by_length(float_model, tokenizer, texts)
_, int8_model = router_lib.int8_classifier(RECORDED / "adapter")
int8_preds, int8_confs = router_lib.classify_by_length(int8_model, tokenizer, texts)
_, head_model = router_lib.int8_classifier_all_linears(RECORDED / "adapter")
head_preds, head_confs = router_lib.classify_by_length(head_model, tokenizer, texts)

print(f"handoff threshold from manifest: {threshold:.2f}")
print(f"messages on test_200: {len(texts)}")
router_lib.print_copy_report("float32", float_preds, float_confs, golds, threshold)
router_lib.print_copy_report("int8", int8_preds, int8_confs, golds, threshold)
changed, handoffs = router_lib.count_changes(float_preds, float_confs, int8_preds, int8_confs, threshold)
print(f"predictions changed by int8: {changed}/{len(texts)} ({changed / len(texts):.1%})")
print(f"hand-off decisions changed by int8: {handoffs}/{len(texts)}")
changed_head, _ = router_lib.count_changes(float_preds, float_confs, head_preds, head_confs, threshold)
print(f"predictions changed with the head in int8 too: {changed_head}/{len(texts)}")
