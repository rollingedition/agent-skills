"""Score every team for the first 3 messages of test_40 with the 135M model, by the summed log-probability of its tokens.
This shows the model's prior, the team it favours before any fine-tuning. The point rests on the most frequent top team and how many messages it tops. The messages are never printed."""

import os

# no network: the pinned model must already be in the local cache
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

# two threads, so the sums add in the same order on every run
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, so greedy decoding repeats
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
rows = router_lib.read_rows("test")
# row numbers of the first three messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 3)
# each team's token ids, padded to the longest name, built once for all messages
table = router_lib.label_token_table(tokenizer)

tops = []
for i in sample:
    scores = router_lib.label_scores(tokenizer, model, table, rows[i][0])
    # index of the highest-scoring team; a tie goes to the lower index
    tops.append(max(range(len(scores)), key=lambda k: (scores[k], -k)))

counts = collections.Counter(tops)
# most frequent top team; a tie in count goes to the lower index
best = min(counts, key=lambda k: (-counts[k], k))

print(f"messages: {len(sample)}")
print(f"distinct top teams: {len(counts)}")
print(f"most frequent top team name: {router_lib.LABELS[best]}")
print(f"most frequent top team: {counts[best]} of {len(sample)}")
