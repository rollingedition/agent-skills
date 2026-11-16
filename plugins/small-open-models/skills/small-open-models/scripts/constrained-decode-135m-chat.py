"""Route the first 6 messages of test_40 with the 135M model through its chat template, decoding only team names.
The template adds the model's default system prompt. The prose quotes this run's accuracy line next to the raw form's, and the messages are never printed."""

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
trie = router_lib.build_trie(tokenizer)
# (text, label index) for every test row, in file order; the index is the gold team
rows = router_lib.read_rows("test")
# row numbers of the first six messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 6)
teams = set(router_lib.LABELS)

results = []
for i in sample:
    # the chat template wraps the message in the model's chat format, with its default system prompt
    text = router_lib.chat_prompt(tokenizer, rows[i][0])
    # the template has already written the special tokens, so the tokenizer adds none
    results.append(router_lib.constrained_team_text(tokenizer, model, trie, text, add_special_tokens=False))
valid = [text in teams for _, text in results]
# the walk's index, never the decoded text, is what counts
right = [index == rows[i][1] for (index, _), i in zip(results, sample)]
given = collections.Counter(text for _, text in results)
# most given team; a tie in count goes to the team listed first
top = min(given, key=lambda team: (-given[team], router_lib.LABELS.index(team)))

print(f"messages: {len(sample)}")
print(f"answers that are a team: {sum(valid)}/{len(sample)}")
print(f"accuracy: {sum(right)}/{len(sample)} ({100 * sum(right) / len(sample):.1f}%)")
print(f"distinct teams given: {len(given)}")
print(f"most given team: {top}, {given[top]}/{len(sample)}")
