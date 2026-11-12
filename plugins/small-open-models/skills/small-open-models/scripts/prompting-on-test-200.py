"""Compare the three prompting variants on test_200, from the recording only. No model is loaded.

recordings/prompting_eval.py wrote one answer per variant and message to examples/data/recorded/prompting-eval/answers.jsonl.
"""

import collections
import json
from pathlib import Path

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

ANSWERS = Path(__file__).resolve().parent / "data" / "recorded" / "prompting-eval" / "answers.jsonl"
teams = set(router_lib.LABELS)
rows = router_lib.read_rows("test")
total = len(router_lib.read_sample("test_200"))

by_variant = collections.defaultdict(list)
with open(ANSWERS) as f:
    for line in f:
        answer = json.loads(line)
        by_variant[answer["variant"]].append(answer)

for variant in sorted(by_variant):
    answers = by_variant[variant]
    outside = sum(answer["team"] not in teams for answer in answers)
    right = sum(answer["label"] == rows[answer["index"]][1] for answer in answers)
    given = collections.Counter(answer["team"] for answer in answers)
    top = min(given, key=lambda team: (-given[team], team))
    gold_top = sum(router_lib.LABELS[rows[answer["index"]][1]] == top for answer in answers)
    print(f"{variant} answers outside the team list: {outside}/{total}")
    print(f"{variant} correct: {right}/{total} ({100 * right / total:.1f}%)")
    print(f"{variant} distinct teams given: {len(given)}")
    print(f"{variant} most given team: {top}, {given[top]}/{total}")
    print(f"{variant} gold for most given team: {gold_top}/{total}")
