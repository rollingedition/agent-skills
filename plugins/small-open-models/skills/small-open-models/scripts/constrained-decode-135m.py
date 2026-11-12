"""Route the first 6 messages of test_40 with the 135M model, decoding only team names, and count how many right answers that gives.
The messages are read from the test split and are never printed."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
trie = router_lib.build_trie(tokenizer)
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40", 6)
teams = set(router_lib.LABELS)

results = [router_lib.constrained_team(tokenizer, model, trie, rows[i][0]) for i in sample]
valid = [text in teams for _, text in results]
right = [index == rows[i][1] for (index, _), i in zip(results, sample)]
given = collections.Counter(text for _, text in results)
top = min(given, key=lambda team: (-given[team], router_lib.LABELS.index(team)))

print(f"messages: {len(sample)}")
print(f"answers that are a team: {sum(valid)}/{len(sample)}")
print(f"accuracy: {sum(right)}/{len(sample)} ({100 * sum(right) / len(sample):.1f}%)")
print(f"distinct teams given: {len(given)}")
print(f"most given team: {top}, {given[top]}/{len(sample)}")
