"""Measure how often the teacher's label matches gold on the training rows it labelled, and its accuracy on test_200
from its recorded answers. The point rests on the agreement line; the example reads recorded answers only."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"

train = router_lib.read_rows("train")
teacher_rows = [json.loads(line) for line in (RECORDED / "teacher-labels" / "labels.jsonl").read_text().splitlines()]
# row["index"] is the row's position in the training file; field 1 of a row is its gold team
agree = sum(row["label"] == train[row["index"]][1] for row in teacher_rows)
n = len(teacher_rows)
print(f"training rows labelled by the teacher: {n}")
print(f"teacher agrees with gold on training rows: {agree}/{n} ({agree / n:.1%})")
print(f"teacher disagrees with gold on training rows: {n - agree}/{n} ({(n - agree) / n:.1%})")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
standin = router_lib.standin_answers()
# sample holds test row positions; field 1 of a test row is its gold team, field 0 its text
golds = [test[i][1] for i in sample]
teacher_preds = [standin[i] for i in sample]
correct = sum(p == g for p, g in zip(teacher_preds, golds))
print(f"messages on test_200 with a teacher answer: {sum(i in standin for i in sample)}/{len(sample)}")
print(f"teacher accuracy on test_200: {correct}/{len(sample)} ({correct / len(sample):.1%})")
