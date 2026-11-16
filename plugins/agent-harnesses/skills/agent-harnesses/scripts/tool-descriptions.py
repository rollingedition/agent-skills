"""The one-sentence description of each tool in the v1 set, the text the model reads beside each schema. The point
rests on the last two printed lines: which chapter 1 tools carry the same sentence in v1, and that finish does not."""
from lib.tools import CH1, V1

print("v1 tools:", len(V1.tools))
for tool in V1.tools:
    print(f"v1 {tool.name}: {tool.description}")
# The chapter 1 tools whose sentence is exactly the one v1 gives the same tool.
shared = [t.name for t in CH1.tools if V1.get(t.name) and V1.get(t.name).description == t.description]
print("ch1 tools with the same sentence in v1:", ", ".join(shared))
print("ch1 finish has the same sentence in v1:", V1.get("finish").description == CH1.get("finish").description)
assert shared == ["read_file", "run_tests"]
