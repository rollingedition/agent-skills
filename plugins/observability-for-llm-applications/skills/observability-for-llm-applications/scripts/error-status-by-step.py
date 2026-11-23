"""Which spans end with ERROR, and what error.type each carries, on the incident day (injected, labelled) and on baseline
day 1 (real). The point rests on the baseline's zero ERROR spans: a wrong route is not a span error, so the status cannot
find it, and the incident's faults look alike from outside."""
from collections import Counter

from lib.dayrun import run_day_traced
from lib.report import fmt_int

real = run_day_traced("2026-12-08", live=False)  # baseline day 1, replayed: no fault is injected into it
real_errors = [row for row in real.spans if row["status"] == "ERROR"]
print("real ERROR spans, baseline day 1 (4B):", fmt_int(len(real_errors)))
assert not real_errors  # the baseline's failures are wrong routes and fallback replies, which set no span status

live = run_day_traced("2026-12-09")  # live: the contacts server runs the injected faults over stdio
rows = live.spans + live.server
errors = [row for row in rows if row["status"] == "ERROR"]
print("ERROR spans, incident day (injected):", fmt_int(len(errors)))
# Each injected fault labels every span it touches, so the label itself tells an injected error from a real one.
assert all(row["attributes"].get("ambrewick.incident.injected") for row in errors)  # every ERROR span is injected
counts = Counter((row["name"], row["attributes"].get("error.type", "none")) for row in errors)
for (name, error_type), count in sorted(counts.items()):
    print(f"{name}, error.type {error_type}, injected: {count}")
