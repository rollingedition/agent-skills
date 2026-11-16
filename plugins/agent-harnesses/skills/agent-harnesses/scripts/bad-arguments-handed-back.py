"""Five bad calls, sent by a ScriptedModel. Each parsed call is run through the v2 tool set and through v1, and each
refusal is the text the model reads on its next step. The point of the prose rests on the v2 lines and the v1 lines
for calls 2 to 5. A call whose JSON is cut off never reaches a schema, so neither set runs it."""
import shutil

from lib.case import scratch_copy
from lib.models import ScriptedModel
from lib.tools import V1, V2, Workspace

CALLS = [
    '<tool_call>{"name": "read_file", "arguments": {"path": "unitcraft/format.py"</tool_call>',
    '<tool_call>{"name": "read_file", "arguments": {}}</tool_call>',
    '<tool_call>{"name": "read_file", "arguments": {"path": "unitcraft/format.py", "lines": 5}}</tool_call>',
    '<tool_call>{"name": "read_file", "arguments": {"path": 3}}</tool_call>',
    '<tool_call>{"name": "read_files", "arguments": {"path": "unitcraft/format.py"}}</tool_call>',
]
scratch = scratch_copy()
ws = Workspace(scratch)
model = ScriptedModel(CALLS)
for number in range(1, len(CALLS) + 1):
    reply = model.reply([], V2.schemas())  # the schemas are sent with each request; a scripted model ignores them
    if reply.malformed:  # the reply parser's reason for a call whose JSON it cannot read
        print(f"call {number}, not run, the JSON is not read: {reply.malformed[0]}")
        continue
    call = reply.tool_calls[0]
    print(f"call {number}, {call['name']}, v2: {V2.call(ws, call['name'], call['arguments']).text}")
    print(f"call {number}, {call['name']}, v1: {V1.call(ws, call['name'], call['arguments']).text}")
shutil.rmtree(scratch, ignore_errors=True)
