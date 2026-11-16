"""Count the router prompt's tokens for each message in test_40, with the 135M model's tokenizer. No model runs. The point rests on the mean line: a day's prompt cost is the mean, not the median, times the number of messages."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

# Only the tokenizer is read from the pinned commit; no weights load.
tokenizer = AutoTokenizer.from_pretrained(SMALL, revision=router_lib._pins()[SMALL])

texts = [text for text, _ in router_lib.read_rows("test")]
# read_sample gives row indices into the test split, in the order the sample lists them.
messages = [texts[i] for i in router_lib.read_sample("test_40")]

# router_prompt builds the same prompt the router sends. encode keeps its default, so any special tokens are counted too.
counts = sorted(len(tokenizer.encode(router_lib.router_prompt(message))) for message in messages)

# The median of an even count is the lower of the two middle values, so it is a whole number of tokens.
median = counts[(len(counts) - 1) // 2]

total = sum(counts)
mean = round(total / len(counts))

print(f"messages: {len(counts)}")
print(f"prompt tokens min: {counts[0]}")
print(f"prompt tokens median: {median}")
print(f"prompt tokens max: {counts[-1]}")
print(f"prompt tokens total: {total}")
print(f"prompt tokens mean, rounded: {mean}")
