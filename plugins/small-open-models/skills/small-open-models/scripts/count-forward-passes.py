"""Run one test_40 message through a classifier and through constrained generation, and count the forward passes. 135M model, no adapter."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from transformers import AutoModelForSequenceClassification  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"
texts = [text for text, _ in router_lib.read_rows("test")]
message = texts[router_lib.read_sample("test_40")[0]]


def count_passes(model, run):
    """Return how many forward calls the model makes while run() executes."""
    calls = []
    handle = model.register_forward_hook(lambda module, args, output: calls.append(1))
    run()
    handle.remove()
    return len(calls)


tokenizer, causal = router_lib.load_model(SMALL)
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
trie = router_lib.build_trie(tokenizer)
classifier = AutoModelForSequenceClassification.from_pretrained(
    SMALL, revision=router_lib._pins()[SMALL], num_labels=len(router_lib.LABELS),
    dtype=torch.float32, attn_implementation="eager",
).eval()
classifier.config.pad_token_id = tokenizer.pad_token_id

classifier_passes = count_passes(classifier, lambda: router_lib.classify(classifier, tokenizer, [message]))
answers = []
generative_passes = count_passes(causal, lambda: answers.append(router_lib.constrained_team(tokenizer, causal, trie, message)))
answer_tokens = len(tokenizer.encode(" " + answers[0][1], add_special_tokens=False))

print(f"classifier forward passes: {classifier_passes}")
print(f"generative forward passes: {generative_passes}")
print(f"answer tokens, end token not counted: {answer_tokens}")
