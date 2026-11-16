"""Count the test_200 messages over 64 tokens and over the 128 that classify() cuts at, then show the cut on one long
message. The prose's point rests on the 128-token line and the before and after lengths; only the tokenizer loads."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

from transformers import AutoTokenizer  # noqa: E402

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
repo = json.loads((RECORDED / "adapter" / "adapter_config.json").read_text())["base_model_name_or_path"]  # the adapter's base model
tokenizer = AutoTokenizer.from_pretrained(repo, revision=router_lib.pinned_revision(repo))  # the pinned revision the model uses

test = router_lib.read_rows("test")         # each row is (message, gold label index)
sample = router_lib.read_sample("test_200") # row numbers of the committed sample
lengths = [len(tokenizer(test[i][0]).input_ids) for i in sample]  # full length in tokens, before any cut
n = len(lengths)
print(f"messages over 64 tokens: {sum(x > 64 for x in lengths)}/{n}")
print(f"messages over 128 tokens where classify() cuts: {sum(x > 128 for x in lengths)}/{n}")

# The cut itself: repeat the text of the first test_200 message until it is longer than 128 tokens,
# then tokenize it with classify()'s settings (truncation on, max_length 128).
long_text = test[sample[0]][0]
while len(tokenizer(long_text).input_ids) <= 128:  # repeat the first message until it runs past the 128-token cut
    long_text = long_text + " " + test[sample[0]][0]
before = len(tokenizer(long_text).input_ids)
after = len(tokenizer(long_text, truncation=True, max_length=128).input_ids)  # the settings classify() passes
print(f"repeated message tokens before the cut: {before}")
print(f"repeated message tokens after the cut: {after}")
print(f"truncation side: {tokenizer.truncation_side}")  # "right" cuts from the end of the text
