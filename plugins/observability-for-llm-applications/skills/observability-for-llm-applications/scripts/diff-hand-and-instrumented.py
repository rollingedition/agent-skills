"""The names the official package emits, set against the GenAI conventions v0.1.0 names this book uses. The table is
examples/lib/names_map.py, which examples/data/genai/build_names_map.py writes by running the package on the recorded
call, on a streamed reply it constructs (for the names a stream adds) and on a call with content events on (for the
event's name). The point rests on
the last printed count: five names differ from v0.1.0, and each one is named here. instrumented-chat-call checks that
the names a live call makes are in the same table."""
from lib.names_map import REGISTRY_VERSION, name_map          # lib first: threads and seeds are fixed before anything else
from importlib.metadata import version

table = name_map()


def status(name, targets):
    """Same when the name is its own v0.1.0 name, or the chat span's type; the two named exceptions get their own
    labels, and the rest are renamed, split or absent."""
    if targets == (name,) or (name == "chat {model}" and targets == ("gen_ai.client.inference",)):
        return "same"
    if name == "gen_ai.client.operation.duration":
        return "wrong instrument for inference"
    if name == "gen_ai.token.type":
        return "replaced by the two token histograms"
    if not targets:
        return "no v0.1.0 name"
    return "split into two" if len(targets) == 2 else "renamed"


statuses = {name: status(name, targets) for name, targets in table.items()}
print("registry version:", REGISTRY_VERSION)
print("package version:", version("opentelemetry-instrumentation-genai-openai"))
print("names the package emits, in the table:", len(table))
print("names the same in v0.1.0:", sum(value == "same" for value in statuses.values()))
for name in sorted(table):
    if statuses[name] != "same":
        print(f"{statuses[name]}, {name}:", " and ".join(table[name]) or "none")
print("names that differ from v0.1.0:", sum(value != "same" for value in statuses.values()))
assert {name for name, value in statuses.items() if value != "same"} == {
    "gen_ai.client.operation.duration", "gen_ai.client.token.usage", "gen_ai.client.operation.time_to_first_chunk",
    "gen_ai.client.operation.time_per_output_chunk", "gen_ai.token.type"}
