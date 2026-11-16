"""Count the forward passes one test_40 message costs a classifier and a generative model, with the 135M model and no adapter. The point rests on the generative line: the model makes one pass for each token it writes, plus one for the end token."""

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
# read_sample gives row indices into the test split; index 0 is the sample's first message.
message = texts[router_lib.read_sample("test_40")[0]]


def count_passes(model, run):
    """Return how many forward calls the model makes while run() executes."""
    calls = []
    # A forward hook on the whole model fires once per call to its forward, so each generation step counts.
    handle = model.register_forward_hook(lambda module, args, output: calls.append(1))
    run()
    handle.remove()
    return len(calls)


tokenizer, causal = router_lib.load_model(SMALL)
# SmolLM2's tokenizer sets a pad token; this line keeps the example working with one that doesn't.
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
# The trie holds each team name's tokens, so constrained_team can write only a team name, one token per pass, then the end token.
trie = router_lib.build_trie(tokenizer)
# The pinned commit from models.toml, and the float32 weights and eager attention that load_model also sets.
# The head is new, with one score per team (77), and untrained here; only the pass count matters.
classifier = AutoModelForSequenceClassification.from_pretrained(
    SMALL, revision=router_lib._pins()[SMALL], num_labels=len(router_lib.LABELS),
    dtype=torch.float32, attn_implementation="eager",
).eval()
# The classification head finds each message's last token through this id, so the config needs it too.
classifier.config.pad_token_id = tokenizer.pad_token_id

classifier_passes = count_passes(classifier, lambda: router_lib.classify(classifier, tokenizer, [message]))
answers = []
generative_passes = count_passes(causal, lambda: answers.append(router_lib.constrained_team(tokenizer, causal, trie, message)))
# answers[0] holds (label index, label text). The text is encoded with a leading space, as the model writes it after "Team:".
answer_tokens = len(tokenizer.encode(" " + answers[0][1], add_special_tokens=False))

print(f"classifier forward passes: {classifier_passes}")
print(f"generative forward passes: {generative_passes}")
print(f"answer tokens, end token not counted: {answer_tokens}")
