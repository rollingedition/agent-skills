"""Count the stand-in's wrong answers, confusions and never-answered teams on test_1001. No model runs."""

import hashlib, json, os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402

router_lib.setup_runtime()

RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
manifest = json.loads((RECORDED / "manifest.json").read_text())
raw = (RECORDED / "answers.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == manifest["output_sha256"]["answers.jsonl"]

records = [json.loads(line) for line in raw.decode().splitlines()]
sample = router_lib.read_sample("test_1001")
assert sorted(r["index"] for r in records) == sorted(sample), "recorded rows differ from test_1001"
assert all(router_lib.LABELS[r["label"]] == r["team"] for r in records), "label and team disagree"
test, LABELS = router_lib.read_rows("test"), router_lib.LABELS

gold_totals = Counter(test[i][1] for i in sample)
answered = Counter(r["label"] for r in records)
pairs = Counter((test[r["index"]][1], r["label"]) for r in records if r["label"] != test[r["index"]][1])
wrong = sum(pairs.values())
# Ties break on the lower gold label index, then the lower answer index.
top = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:3]
never = sorted(team for k, team in enumerate(LABELS) if answered[k] == 0)

print(f"messages: {len(sample)}")
print(f"wrong answers: {wrong}")
print(f"wrong rate: {100 * wrong / len(sample):.1f}% ({wrong} of {len(sample)})")
for rank, ((gold, answer), count) in enumerate(top, start=1):
    print(f"pair {rank} count: {count}")
    print(f"pair {rank} gold: {LABELS[gold]}")
    print(f"pair {rank} answer: {LABELS[answer]}")
    print(f"pair {rank} of gold team: {count}/{gold_totals[gold]}")
print(f"teams never answered: {len(never)}")
for rank, team in enumerate(never, start=1):
    gold = LABELS.index(team)
    count, answer = max(((c, a) for (g, a), c in pairs.items() if g == gold), key=lambda ca: (ca[0], -ca[1]))
    print(f"never answered {rank} team: {team}")
    print(f"never answered {rank} messages: {gold_totals[gold]}")
    print(f"never answered {rank} most often as: {LABELS[answer]}")
    print(f"never answered {rank} most often count: {count}")
