"""The JSON schema pydantic makes for a read with a line limit: its bounds, its default and the descriptions the
model reads before it calls. The point of the prose rests on the max_lines lines: the bounds, the default and the
description."""
from lib.tools import LinesArgs

schema = LinesArgs.model_json_schema()
limit = schema["properties"]["max_lines"]  # the schema of the one field with a bound
print("required:", ", ".join(schema["required"]))
print("max_lines minimum:", limit["minimum"])
print("max_lines maximum:", limit["maximum"])
print("max_lines default:", limit["default"])
print("max_lines description:", limit["description"])
print("path description:", schema["properties"]["path"]["description"])
# LinesArgs has no extra="forbid", so its schema says nothing about other keys. The tool classes do forbid them.
assert "additionalProperties" not in schema
