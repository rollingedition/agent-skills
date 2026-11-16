"""Write a model's team answers in the stand-in's JSONL shape, then check record_answers against the stand-in's recording.
The line to read is the last one printed, which counts the lines that match the recording. The stand-in here replays
that recording, so no model runs."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import tempfile  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()


def record_answers(call_model, messages, path):
    """Write one JSONL line per (index, text); call_model(text) returns (team, logprob)."""
    with open(path, "w") as out:
        for index, text in messages:
            team, logprob = call_model(text)
            if team not in router_lib.LABELS:
                raise ValueError("the model returned a name that is not a team")
            label = router_lib.LABELS.index(team)  # stored as the label, the same encoding as the gold labels
            row = {"index": index, "label": label, "team": team, "logprob": logprob}
            out.write(json.dumps(row) + "\n")


RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"
rows = router_lib.read_rows("test")  # each row is (text, gold label)
sample = router_lib.read_sample("test_40")
messages = [(i, rows[i][0]) for i in sample]  # element 0 of a row is its text, which the model reads
with open(RECORDING) as f:
    recording_lines = f.read().splitlines()
recorded = {json.loads(line)["index"]: json.loads(line) for line in recording_lines}  # keyed by message index
by_text = {rows[i][0]: (recorded[i]["team"], recorded[i]["logprob"]) for i in sample}  # keyed by text, not index


def standin(text):
    """Stand in for a model: return the recorded team and logprob for this message."""
    return by_text[text]


with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "answers.jsonl")
    record_answers(standin, messages, path)
    with open(path) as f:
        written = f.read().splitlines()

matching = sum(line in recording_lines for line in written)  # a line matches when it equals a recorded line exactly
print(f"messages written: {len(written)}")
print(f"lines matching the recording: {matching}/{len(written)}")
