"""Count baseline day 1's message times into the buckets the GenAI conventions advise for the agent's duration histogram, then
estimate the p95 from the bucket counts and set it beside the nearest-rank p95 of the raw values. The estimate spreads each
bucket's values evenly across it, and the p95 falls in one bucket, so the buckets can only place the estimate inside it."""

from lib import genai
from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bucket_counts, nearest_rank

import math

EDGES_S = genai.BUCKETS["gen_ai.client.invoke_agent.duration"]   # the conventions' advised upper bounds, in seconds
print("GenAI conventions version:", genai.REGISTRY_VERSION)
print("bucket boundaries, GenAI conventions, seconds:", ", ".join(str(edge) for edge in EDGES_S))
runs = run_day("2026-12-08")
times = [run.replied_ns - run.arrived_ns for run in runs]
n = len(times)
edges = [round(edge * 1_000_000_000) for edge in EDGES_S]      # integer nanoseconds, as every time here is
counts = bucket_counts(times, edges)                           # a value sits in the bucket whose upper edge it does not exceed
print("messages (n):", fmt_int(n))
for index, count in enumerate(counts):
    low = edges[index - 1] if index else 0                     # a bucket starts at the upper edge of the one before it
    if index < len(edges):
        print(f"bucket above {fmt_ms(low)} up to {fmt_ms(edges[index])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
    else:
        print(f"bucket above {fmt_ms(low)}: {fmt_int(count)} messages, {fmt_share(count, n)}")

exact = nearest_rank(times, 95)
rank = math.ceil(95 * n / 100)                                 # the nearest-rank position of the p95
index = next(i for i, edge in enumerate(edges) if exact <= edge)   # the bucket that holds the exact p95
low = edges[index - 1] if index else 0                         # its lower edge, as above; the first starts at zero
below = sum(counts[:index])                                    # messages in the buckets under it
estimate = low + round((rank - below) * (edges[index] - low) / counts[index])
print("bucket holding the p95, lower edge:", fmt_ms(low))
print("bucket holding the p95, upper edge:", fmt_ms(edges[index]))
print("messages in that bucket:", fmt_int(counts[index]))
print("messages at or below its lower edge:", fmt_int(below))
print("p95, nearest rank of the raw values:", fmt_ms(exact))
print("p95, estimated from the bucket counts:", fmt_ms(estimate))
print("estimate minus the nearest-rank p95:", fmt_ms(estimate - exact))
assert low < exact <= edges[index]                             # the exact p95 lies in the bucket that holds it
assert abs(estimate - exact) > 500_000_000                     # the bucket estimate is more than half a second off
