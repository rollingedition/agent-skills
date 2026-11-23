"""Give one model call two kinds: CLIENT when the model sits behind an endpoint, as the trace shows it, and INTERNAL
when the same assistant runs the model in process. Then run the validator on both.

The point rests on the two model-call kind lines and on the zero findings: the registry allows INTERNAL for an
in-process model (it says MAY), and the validator accepts it when the call names no server. An endpoint span marked
INTERNAL is flagged, because it names one."""
from lib.dayrun import DAY, RECORDING, run_day_traced
from lib.genai import REGISTRY_VERSION, validate
from lib.replay import Replay


class InProcess:
    """The recorded model, run as if it shared the assistant's process: the same answers, and no endpoint."""

    in_process = True

    def __init__(self, replay):
        self._replay = replay

    def reply(self, request):
        return self._replay.reply(request)


rows = run_day_traced(DAY, ["809"], live=False).spans  # a devices message: a route and an answer call, behind an endpoint
local = run_day_traced(DAY, ["809"], backend=InProcess(Replay(RECORDING)), live=False).spans  # the same model in process
endpoint = next(row for row in rows if row["name"].startswith("chat "))
in_process = next(row for row in local if row["name"].startswith("chat "))
retrieval = next(row for row in rows if row["name"] == "retrieval")
root = next(row for row in rows if row["parent_span_id"] is None)
marked = dict(endpoint, kind="INTERNAL")  # the endpoint's span, wrongly marked as in process

print("GenAI conventions version:", REGISTRY_VERSION)
print("model call kind, behind an endpoint:", endpoint["kind"])
print("model call kind, in process:", in_process["kind"])
address, port = endpoint["attributes"]["server.address"], endpoint["attributes"]["server.port"]
print("server the endpoint span names:", f"{address}:{port}")
print("findings on the in-process span:", len(validate(in_process)))
print("findings on the endpoint span marked INTERNAL:", len(validate(marked)))
print("retrieval span kind:", retrieval["kind"])
print("agent span kind:", root["kind"])
assert validate(endpoint) == [] and validate(in_process) == []  # both kinds are the registry's
assert "server.address" not in in_process["attributes"]  # an in-process model names no server
assert len(validate(marked)) == 1 and "kind is INTERNAL" in validate(marked)[0]
assert validate(retrieval) == [] and validate(root) == []  # INTERNAL is the registry's kind for these two types
