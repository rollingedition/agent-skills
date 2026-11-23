"""Which attributes may label the assistant's duration metric (chapter 9, `cardinality`).

A metric keeps one series for each distinct set of attribute values, and each series is stored and queried. The
registry's attributes give one series for a message's operation on a normal day. A route gives a few more. A user ID
gives one series per user, so the count grows with the traffic and no dashboard can read it. The assistant's live meter
keeps the registry's attributes only, so its count is the first line. The other two are what the same messages would
give with another attribute added, counted from their spans."""
from lib.dayrun import run_day_traced
from lib.metrics import DURATION, METRIC_ATTRIBUTES, make_alert_meter_provider
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
reader = InMemoryMetricReader()
provider = make_alert_meter_provider(reader, service_instance_id=f"{DAY}-cardinality")
traced = run_day_traced(DAY, live=False, meter_provider=provider)  # the assistant's live meter, registry attributes only
messages = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "invoke_agent"]
users = {row["attributes"]["ambrewick.user.id"] for row in messages}
routes = {row["attributes"]["ambrewick.route"] for row in messages if row["attributes"].get("ambrewick.route")}
print("messages:", fmt_int(len(messages)))
print("distinct users:", fmt_int(len(users)))
print("distinct routes:", fmt_int(len(routes)))


def series(reader, name: str | None = None) -> int:
    """The number of series a reader holds, for one metric when a name is given (one per distinct attribute set)."""
    reader.collect()
    return sum(len(metric.data.data_points) for resource in reader.get_metrics_data().resource_metrics
               for scope in resource.scope_metrics for metric in scope.metrics if name in (None, metric.name))


def series_with(extra: tuple[str, ...]) -> int:
    """The number of series the duration histogram holds when each message carries the registry's attributes and
    the `extra` ones. Values are the messages' real durations; only the count of attribute sets matters here."""
    own = InMemoryMetricReader()
    histogram = make_alert_meter_provider(own, service_instance_id=f"{DAY}-cardinality").get_meter("cardinality") \
        .create_histogram(DURATION["invoke_agent"], unit="s")
    for row in messages:
        attrs = row["attributes"]
        kept = {key: attrs[key] for key in METRIC_ATTRIBUTES + extra if key in attrs}
        histogram.record((row["end_ns"] - row["start_ns"]) / 1_000_000_000, kept)
    return series(own)


registry = series(reader, DURATION["invoke_agent"])
with_route = series_with(("ambrewick.route",))
with_user = series_with(("ambrewick.user.id",))
print("series, registry attributes:", fmt_int(registry))
print("series, registry attributes and route:", fmt_int(with_route))
print("series, registry attributes and user ID:", fmt_int(with_user))
assert registry == 1                       # on a normal day every message is a success with one attribute set
assert with_user == len(users)             # a user ID makes one series per user, and no two users share one
assert with_user > with_route > registry   # each attribute that varies multiplies the series
