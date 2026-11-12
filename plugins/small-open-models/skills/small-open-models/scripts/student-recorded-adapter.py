"""Evaluate the distilled student banking77-distilled-v1 on test_200 beside banking77-lora-v1. The student's
hand-off threshold is chosen on dev by the book's rule; the adapters are loaded and scored live, nothing is trained."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"

tokenizer, student = router_lib.load_classifier(RECORDED / "distill-student" / "adapter")
DEV_N = 500  # the first 500 of the 1,003 dev messages: the run's time budget under two CPUs
threshold, reached = router_lib.dev_threshold(student, tokenizer, target=0.90, n=DEV_N)
print(f"dev messages used: {DEV_N} of {len(router_lib.read_sample('dev'))}")
print(f"dev threshold reaching 0.90 accuracy not handed off: {'yes' if reached else 'no'}")
print(f"student threshold chosen on dev: {threshold:.2f}")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]
student_preds, student_confs = router_lib.classify(student, tokenizer, texts)
router_lib.print_copy_report("banking77-distilled-v1", student_preds, student_confs, golds, threshold)

lora = json.loads((RECORDED / "lora-full" / "manifest.json").read_text())
_, lora_model = router_lib.load_classifier(RECORDED / "lora-full" / "adapter")
lora_preds, lora_confs = router_lib.classify(lora_model, tokenizer, texts)
router_lib.print_copy_report("banking77-lora-v1", lora_preds, lora_confs, golds, lora["handoff_threshold"])

teacher = router_lib.standin_answers()
teacher_preds = [teacher[i] for i in sample]
matches = sum(s == t for s, t in zip(student_preds, teacher_preds))
wrong = [k for k in range(len(sample)) if student_preds[k] != golds[k]]
wrong_like_teacher = sum(student_preds[k] == teacher_preds[k] for k in wrong)
print(f"student answers equal to teacher answers on test_200: {matches}/{len(sample)} ({matches / len(sample):.1%})")
print(f"student errors on test_200: {len(wrong)}/{len(sample)} ({len(wrong) / len(sample):.1%})")
print(f"student errors equal to the teacher's answer: {wrong_like_teacher}/{len(wrong)}")
