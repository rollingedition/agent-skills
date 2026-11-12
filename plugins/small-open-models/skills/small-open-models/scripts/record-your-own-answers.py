"""Record a model's team answers in the stand-in's JSONL shape, then check the demo against the recording.
The demo's stand-in reads the recorded answers, so no model runs here."""

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
            label = router_lib.LABELS.index(team)
            row = {"index": index, "label": label, "team": team, "logprob": logprob}
            out.write(json.dumps(row) + "\n")


RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40")
messages = [(i, rows[i][0]) for i in sample]
with open(RECORDING) as f:
    recording_lines = f.read().splitlines()
recorded = {json.loads(line)["index"]: json.loads(line) for line in recording_lines}
by_text = {rows[i][0]: (recorded[i]["team"], recorded[i]["logprob"]) for i in sample}


def standin(text):
    """Stand in for a model: return the recorded team and logprob for this message."""
    return by_text[text]


with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "answers.jsonl")
    record_answers(standin, messages, path)
    with open(path) as f:
        written = f.read().splitlines()

matching = sum(line in recording_lines for line in written)
print(f"messages written: {len(written)}")
print(f"lines matching the recording: {matching}/{len(written)}")
