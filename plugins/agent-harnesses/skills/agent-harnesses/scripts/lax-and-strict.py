"""Pydantic's default (lax) mode and strict mode, given the same values for an int field: lax takes the string "50"
and the bool True as ints, strict refuses both, and each refusal names its error type. The point of the prose rests
on the last lines: on a string field the two modes refuse the same values, and the two tool sets' schemas differ
only in their titles."""
from lib.tools import LinesArgs, PathArg, StrictLinesArgs, StrictPathArg, V1, V2
from pydantic import ValidationError

values = [("str 50", "50"), ("int 50", 50), ("bool True", True), ("float 2.0", 2.0), ("float 2.5", 2.5)]
outcomes = {}
for label, value in values:
    for mode, model in (("lax", LinesArgs), ("strict", StrictLinesArgs)):
        try:
            model.model_validate({"path": "unitcraft/format.py", "max_lines": value})
            outcomes[mode, label] = "accepted"
        except ValidationError as exc:
            outcomes[mode, label] = exc.errors()[0]["type"]  # the first error's type, which a refusal names
        print(f"{mode}, max_lines {label}: {outcomes[mode, label]}")
assert outcomes["lax", "str 50"] == "accepted" and outcomes["strict", "str 50"] == "int_type"

# The case's tools take only strings. On a string field the modes agree, because lax mode does not turn a number,
# a flag or nothing into a string.
for label, value in [("str a.py", "a.py"), ("int 3", 3), ("float 3.5", 3.5), ("bool True", True), ("None", None),
                     ("list", []), ("object", {})]:
    results = {}
    for mode, model in (("lax", PathArg), ("strict", StrictPathArg)):
        try:
            model.model_validate({"path": value})
            results[mode] = "accepted"
        except ValidationError as exc:
            results[mode] = exc.errors()[0]["type"]  # the first error's type, which a refusal names
        print(f"{mode}, path {label}: {results[mode]}")
    assert results["lax"] == results["strict"]


def untitled(node):
    """A schema with its titles removed, so the two tool sets can be compared on everything else."""
    if isinstance(node, dict):
        return {key: untitled(value) for key, value in node.items() if key != "title"}
    if isinstance(node, list):
        return [untitled(item) for item in node]
    return node


same = [untitled(a.schema()) == untitled(b.schema()) for a, b in zip(V1.tools, V2.tools)]
print("v1 and v2 schemas differ before titles are removed:", any(a.schema() != b.schema() for a, b in zip(V1.tools, V2.tools)))
print("v1 and v2 schemas equal once titles are removed:", all(same))
assert all(same)
