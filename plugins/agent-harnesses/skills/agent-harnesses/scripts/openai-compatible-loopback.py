"""The OpenAI-compatible adapter, run live against a loopback stub that serves the bodies recorded from llama.cpp's own
server. The line that matters is "raw text": the server put the call in the message content as text, with no tool_calls
field, so the adapter parses the text, and the tool's own model accepts the arguments. Needs
recordings/openai_compatible.py to have been run; until then this raises."""
import json

from lib.case import load_tasks
from lib.models import first_step, loopback_model, serve_recorded
from lib.tools import CH1

task = load_tasks(only=["T-01"])[0]
messages, tools = first_step(task, CH1)
bodies: list[str] = []
with serve_recorded("openai-compatible") as base_url:
    model = loopback_model(base_url, on_body=bodies.append)
    first = model.reply(messages, tools)
    second = model.reply(messages, tools)
assert first.text.lstrip().startswith("<tool_call>"), "the server should return the call as text"
assert "tool_calls" not in json.loads(bodies[0])["choices"][0]["message"], "the recorded body has a structured tool_calls field"
assert len(first.tool_calls) == 1 and first.tool_calls[0]["name"] == "read_file", "the first step is one read_file call"
assert not first.malformed, "the call should parse"
CH1.get("read_file").args.model_validate(first.tool_calls[0]["arguments"])  # raises if the arguments do not fit the tool
assert first.text == second.text, "the two recorded responses differ"
print(f"requests: {len(bodies)}")
print("raw text:", json.dumps(first.text))
print("structured tool_calls field: absent")
print(f"tool calls: {len(first.tool_calls)}")
print("call:", first.tool_calls[0]["name"], json.dumps(first.tool_calls[0]["arguments"], sort_keys=True))
print(f"malformed: {len(first.malformed)}")
print(f"prompt tokens: {first.prompt_tokens}")
print(f"completion tokens: {first.completion_tokens}")
print(f"finish reason: {first.finish_reason}")
