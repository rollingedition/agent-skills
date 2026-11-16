"""The edit_file call from step 3 of the task-set recording's T-01 run, read from its stored reply. Its old text drops
the quotes around the f-strings and the closing quote of separator = "."; the printed old text shows it. The point of
the prose rests on the two results: the v2 error names the nearest lines of the file, with their quotes, and the v1
error only says the text is missing."""
import json
import shutil

from lib.case import DATA, scratch_copy
from lib.models import ScriptedModel
from lib.tools import V1, V2, Workspace

rows = [json.loads(line) for line in (DATA / "recorded" / "task-set" / "replies.jsonl").read_text().splitlines()]
stored = next(row for row in rows if row["run"] == "T-01" and row["step"] == 3)  # steps count from 1
call = ScriptedModel([stored["text"]]).reply([], V2.schemas()).tool_calls[0]  # the recorded reply, read back
scratch = scratch_copy()
ws = Workspace(scratch)
print("call:", call["name"], call["arguments"]["path"])
print("old text:")
print(call["arguments"]["old"])
print("v1 result:", V1.call(ws, call["name"], call["arguments"]).text)
v2 = V2.call(ws, call["name"], call["arguments"]).text
print("v2 result:")
print(v2)
assert 'text = f"{whole}{separator}{frac}"' in v2
shutil.rmtree(scratch, ignore_errors=True)
