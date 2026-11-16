"""The stored chapter-1 run is the recording its manifest describes, and replaying it hands the loop each stored reply text
exactly. The prompt and the check hash to the manifest's values, the first request hashes to the reply row stored with it,
and the stored replies add up to the manifest's counts. The run is then replayed through the loop, which refuses any request
that differs from its recorded hash, and each replayed text is compared with its stored text. No model file is loaded."""
from contextlib import closing

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import RECORDED_SAMPLING, ReplayModel, TextCapture, first_step, load_recording, request_hash, same_texts, stored_totals
from lib.prompts import prompt_sha256
from lib.tasks import check_sha256
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
manifest, rows = load_recording("chapter-1-t01")
messages, tools = first_step(task, CH1)
assert manifest["prompt_sha256"] == prompt_sha256(CH1.system, CH1.descriptions()), "the prompt changed since recording"
assert manifest["check_sha256"] == check_sha256(task), "the check changed since recording"
assert rows[0]["request_sha256"] == request_hash(messages, tools), "the first request differs from the stored reply row"
assert len(rows) == manifest["steps"], "the stored replies and the manifest disagree on the step count"
prompt_tokens, completion_tokens = stored_totals(manifest, rows)
assert manifest["sampling"] == RECORDED_SAMPLING, "the recording's sampling differs from the settings the adapters send"

capture = TextCapture(ReplayModel("chapter-1-t01", "T-01"))
with closing(run_task(capture, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())) as run:
    steps, ended = run.steps, run.ended
compared = same_texts(rows, capture.texts)
assert steps == manifest["steps"] and ended == manifest["ended"], "the replay did not end as the manifest records"
print(f"stored replies: {len(rows)}")
print(f"prompt tokens: {prompt_tokens}")
print(f"completion tokens: {completion_tokens}")
for key in ("temperature", "top_k", "seed"):
    print(f"{key}: {manifest['sampling'][key]}")
print(f"reply texts compared exactly: {compared}")
print(f"steps: {steps}")
print(f"ended: {ended}")
